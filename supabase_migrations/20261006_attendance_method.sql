alter table public.attendance_logs
    add column if not exists attendance_method text;

comment on column public.attendance_logs.attendance_method is
    'Attendance capture method, e.g. face, voice, or live_face. NULL indicates a legacy record with no stored method.';

notify pgrst, 'reload schema';
