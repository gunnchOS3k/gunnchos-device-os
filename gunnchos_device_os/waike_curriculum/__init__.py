"""WAIKE 18-course product surface (device-os).

Owner IDs come from waike-research-ops ``programs/`` + the 18-course charter list.
This package ships digitally executable *seeds* (lesson + lab + packets), not a
finished 8-week LMS. Full curriculum complete is never claimed from this module.
"""

from gunnchos_device_os.waike_curriculum.catalog import (
    COURSE_IDS,
    COURSES,
    LEGACY_PACK_TO_COURSE,
    course_by_id,
    resolve_course_id,
)

__all__ = [
    "COURSE_IDS",
    "COURSES",
    "LEGACY_PACK_TO_COURSE",
    "course_by_id",
    "resolve_course_id",
]
