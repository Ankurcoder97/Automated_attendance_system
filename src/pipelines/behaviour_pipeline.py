from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


ENGAGEMENT_LEVELS = (
    (80, "HIGH"),
    (60, "MODERATE"),
    (40, "LOW"),
    (0, "VERY LOW"),
)


@dataclass
class BehaviourSnapshot:
    student_id: int
    event_type: str
    confidence: float
    metadata: dict = field(default_factory=dict)


class ObservableBehaviourDetector:
    """Transparent behaviour interface.

    The current project has reliable face recognition only. This detector therefore
    records observable visibility signals and exposes unsupported detectors without
    inventing phone, drowsiness, gaze, or head-pose scores.
    """

    unavailable_features = {
        "head_pose": "No head-pose landmark classifier is configured.",
        "gaze": "No gaze estimation model is configured.",
        "phone_usage": "No phone/object detector is configured.",
        "drowsiness": "No eye-aspect-ratio or blink model is configured.",
    }

    def detect(self, detected_student_ids, enrolled_student_ids):
        detected = {int(student_id) for student_id in detected_student_ids}
        enrolled = {int(student_id) for student_id in enrolled_student_ids}
        snapshots = []

        for student_id in enrolled:
            if student_id in detected:
                snapshots.append(
                    BehaviourSnapshot(
                        student_id=student_id,
                        event_type="FOCUSED",
                        confidence=0.75,
                        metadata={"signals": ["face_present"], "limitations": self.unavailable_features},
                    )
                )
            else:
                snapshots.append(
                    BehaviourSnapshot(
                        student_id=student_id,
                        event_type="AWAY",
                        confidence=0.5,
                        metadata={"signals": ["student_not_visible"], "limitations": self.unavailable_features},
                    )
                )

        return snapshots


def engagement_from_durations(focused_duration, distracted_duration, phone_usage_duration, drowsy_duration, away_duration):
    observed = focused_duration + distracted_duration + phone_usage_duration + drowsy_duration + away_duration
    if observed <= 0:
        return 0.0, "VERY LOW"

    penalty = (
        distracted_duration * 0.45
        + phone_usage_duration * 0.8
        + drowsy_duration * 0.7
        + away_duration * 0.65
    )
    score = max(0.0, min(100.0, ((focused_duration - penalty) / observed) * 100))
    return round(score, 2), engagement_level(score)


def engagement_level(score):
    for threshold, label in ENGAGEMENT_LEVELS:
        if score >= threshold:
            return label
    return "VERY LOW"


def utc_now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
