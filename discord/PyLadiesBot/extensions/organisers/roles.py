"""Data structure for role IDs."""

import attrs


@attrs.define
class Roles:
    """Role mapping for the organisers extension."""

    organisers: int
    volunteers: int
    sponsors: int
    speakers: int
    participants: int
