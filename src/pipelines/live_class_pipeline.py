from __future__ import annotations

import threading
import time
from collections import defaultdict
from datetime import datetime

import av

from src.database.db import (
    create_attendance,
    create_attendance_once,
    end_behaviour_event,
    upsert_behaviour_event,
    upsert_student_analytics,
)
from src.pipelines.behaviour_pipeline import (
    ObservableBehaviourDetector,
    engagement_from_durations,
    utc_now_iso,
)
from src.pipelines.face_pipeline import predict_attendance


EVENT_DURATION_FIELDS = {
    "FOCUSED": "focused_duration",
    "DISTRACTED": "distracted_duration",
    "PHONE_USAGE": "phone_usage_duration",
    "DROWSY": "drowsy_duration",
    "AWAY": "away_duration",
}


class LiveClassProcessor:
    def __init__(self, session_id, subject_id, enrolled_students, sample_interval=4, required_confirmations=2):
        self.session_id = session_id
        self.subject_id = subject_id
        self.enrolled_students = enrolled_students
        self.enrolled_ids = [int(row["student_id"]) for row in enrolled_students]
        self.sample_interval = sample_interval
        self.required_confirmations = required_confirmations
        self.detector = ObservableBehaviourDetector()
        self.lock = threading.Lock()
        self.next_sample_at = 0
        self.confirmations = defaultdict(int)
        self.present_ids = set()
        self.current_events = {}
        self.event_started_at = {}
        self.durations = defaultdict(lambda: defaultdict(int))
        self.last_event_at = {}
        self.total_faces_seen = 0
        self.last_error = None
        self.last_processed_at = None

    def recv(self, frame):
        now = time.time()
        if now >= self.next_sample_at:
            self.next_sample_at = now + self.sample_interval
            image = frame.to_ndarray(format="rgb24")
            self.process_frame(image, now)
        return frame

    def process_frame(self, image_np, now=None):
        now = now or time.time()
        try:
            detected, _, face_count = predict_attendance(image_np)
            detected_ids = {int(student_id) for student_id in detected.keys()}
            self.total_faces_seen = face_count
            self._update_attendance(detected_ids)
            self._update_behaviour(detected_ids, now)
            self.last_error = None
            self.last_processed_at = datetime.now().strftime("%H:%M:%S")
        except Exception as exc:
            self.last_error = str(exc)

    def _update_attendance(self, detected_ids):
        timestamp = utc_now_iso()
        for student_id in detected_ids.intersection(self.enrolled_ids):
            self.confirmations[student_id] += 1
            if self.confirmations[student_id] < self.required_confirmations or student_id in self.present_ids:
                continue

            log = {
                "student_id": student_id,
                "subject_id": self.subject_id,
                "session_id": self.session_id,
                "timestamp": timestamp,
                "is_present": True,
                "attendance_method": "live_face",
            }
            try:
                create_attendance_once(log)
                self.present_ids.add(student_id)
            except Exception as exc:
                self.last_error = f"Attendance sync failed: {exc}"

    def _update_behaviour(self, detected_ids, now):
        snapshots = self.detector.detect(detected_ids, self.enrolled_ids)
        for snapshot in snapshots:
            student_id = int(snapshot.student_id)
            previous_event = self.current_events.get(student_id)
            previous_at = self.last_event_at.get(student_id, now)
            elapsed = max(0, int(now - previous_at))

            if previous_event:
                self.durations[student_id][EVENT_DURATION_FIELDS[previous_event]] += elapsed

            if previous_event and previous_event != snapshot.event_type:
                total_event_duration = max(0, int(now - self.event_started_at.get(student_id, now)))
                end_behaviour_event(self.session_id, student_id, previous_event, utc_now_iso(), total_event_duration)

            if previous_event != snapshot.event_type:
                upsert_behaviour_event(
                    student_id=student_id,
                    subject_id=self.subject_id,
                    session_id=self.session_id,
                    event_type=snapshot.event_type,
                    confidence=snapshot.confidence,
                    metadata=snapshot.metadata,
                )
                self.event_started_at[student_id] = now

            self.current_events[student_id] = snapshot.event_type
            self.last_event_at[student_id] = now
            self._sync_student_analytics(student_id)

    def _sync_student_analytics(self, student_id):
        durations = self.durations[student_id]
        focused = durations["focused_duration"]
        distracted = durations["distracted_duration"]
        phone = durations["phone_usage_duration"]
        drowsy = durations["drowsy_duration"]
        away = durations["away_duration"]
        present = focused + distracted + phone + drowsy
        score, level = engagement_from_durations(focused, distracted, phone, drowsy, away)
        upsert_student_analytics(
            {
                "student_id": student_id,
                "subject_id": self.subject_id,
                "session_id": self.session_id,
                "present_duration": present,
                "focused_duration": focused,
                "distracted_duration": distracted,
                "phone_usage_duration": phone,
                "drowsy_duration": drowsy,
                "away_duration": away,
                "engagement_score": score,
                "engagement_level": level,
                "updated_at": utc_now_iso(),
            }
        )

    def finalize(self):
        now_iso = utc_now_iso()
        for student_id, event_type in list(self.current_events.items()):
            elapsed = max(0, int(time.time() - self.last_event_at.get(student_id, time.time())))
            field = EVENT_DURATION_FIELDS.get(event_type)
            if field:
                self.durations[student_id][field] += elapsed
            total_event_duration = max(0, int(time.time() - self.event_started_at.get(student_id, time.time())))
            end_behaviour_event(self.session_id, student_id, event_type, now_iso, total_event_duration)
            self._sync_student_analytics(student_id)

        absent_logs = []
        for student_id in self.enrolled_ids:
            if student_id in self.present_ids:
                continue
            absent_logs.append(
                {
                    "student_id": student_id,
                    "subject_id": self.subject_id,
                    "session_id": self.session_id,
                    "timestamp": now_iso,
                    "is_present": False,
                    "attendance_method": "live_face",
                }
            )
        if absent_logs:
            create_attendance(absent_logs)

    def snapshot(self):
        with self.lock:
            total = len(self.enrolled_ids)
            scores = []
            for student_id in self.enrolled_ids:
                durations = self.durations[student_id]
                score, _ = engagement_from_durations(
                    durations["focused_duration"],
                    durations["distracted_duration"],
                    durations["phone_usage_duration"],
                    durations["drowsy_duration"],
                    durations["away_duration"],
                )
                scores.append(score)
            average = round(sum(scores) / len(scores), 2) if scores else 0.0
            return {
                "students_detected": len([sid for sid in self.enrolled_ids if self.confirmations[sid] > 0]),
                "present": len(self.present_ids),
                "absent": max(total - len(self.present_ids), 0),
                "total": total,
                "average_engagement": average,
                "last_processed_at": self.last_processed_at,
                "last_error": self.last_error,
            }
