import typing

import attrs


@attrs.define
class AutoResponse:
    id: str = attrs.field(converter=str)
    author: str = attrs.field(converter=str)
    auto_deletion: int
    message_triggers: list[str]
    content: str
    enabled: typing.Optional[bool] = attrs.field(
        kw_only=True,
        converter=attrs.converters.default_if_none(True),
    )

    @classmethod
    def from_db(cls, data: dict):
        return cls(
            id=data["_id"],
            author=data["author"],
            auto_deletion=data["auto_deletion"],
            message_triggers=data["message_triggers"],
            content=data["response_message"],
            enabled=data.get("enabled"),
        )


# TODO: broken & unused
@attrs.define
class ServerConfig:
    id: str = attrs.field(converter=str)
    premium_support_log_channel: typing.Optional[int] = attrs.field(kw_only=True)
    general_admin_log_channel: typing.Optional[int] = attrs.field(kw_only=True)
    mod_log_channel: typing.Optional[int] = attrs.field(kw_only=True)
    responder_channels: typing.Optional[list[str]] = attrs.field(kw_only=True)

    @classmethod
    def from_db(cls, data: dict):
        return cls(
            id=data["_id"],
            premium_support_log_channel=data.get("author"),
            general_admin_log_channel=data.get("auto_deletion"),
            mod_log_channel=data.get("moderation"),
            responder_channels=data.get("response_message"),
        )


@attrs.define
class VolunteerMetric:
    id: str = attrs.field(converter=str)
    messages: int
    tags: int
    is_volunteer: typing.Optional[bool] = attrs.field(
        kw_only=True, converter=attrs.converters.default_if_none(True), default=True
    )
    is_trial: typing.Optional[bool] = attrs.field(
        kw_only=True, converter=attrs.converters.default_if_none(False), default=False
    )


@attrs.define
class MonthlyVolunteerMetrics:
    id: str = attrs.field(converter=str)  # yyyy
    # These next two are dicts in the DB, but in our POV we just want a list of people.
    staff: list[VolunteerMetric] = attrs.field(factory=list[VolunteerMetric])
    trial_staff: list[VolunteerMetric] = attrs.field(factory=list[VolunteerMetric])

    @classmethod
    def from_db(cls, data: dict):
        volunteers = []
        trials = []
        if vols := data.get("volunteer", {}):
            for uid, udata in vols.items():
                volunteers.append(
                    VolunteerMetric(
                        uid,
                        udata.get("msg_count", 0),
                        udata.get("tag_count", 0),
                        is_volunteer=True,
                    )
                )

        if trls := data.get("trial", {}):
            for uid, udata in trls.items():
                trials.append(
                    VolunteerMetric(
                        uid,
                        udata.get("msg_count", 0),
                        udata.get("tag_count", 0),
                        is_volunteer=False,
                        is_trial=True,
                    )
                )

        return cls(
            id=data["_id"],
            staff=volunteers,
            trial_staff=trials,
        )


@attrs.define
class Tag:
    name: str
    author_id: str
    content: str
    created_at: str
    updated_at: typing.Optional[str] = attrs.field(kw_only=True, default=None)
    lifetime_uses: int
    aliases: list[str] = attrs.field(factory=list)

    @classmethod
    def from_db(cls, data: dict):
        return cls(
            name=data["_id"],
            aliases=data["aliases"],
            author_id=data["author"],
            content=data["content"],
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
            lifetime_uses=data["use_count"],
        )
