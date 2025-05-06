from resources.models.autoresponse import AutoResponse

stored_trigger_map: dict[str, AutoResponse] = dict()
autoresponder_channels: dict[str, set] = dict()
