# ← 4 Spaces Einrückung – gehört zur Klasse!
    async def _receiver(self) -> None:
        assert self._ws is not None
        ws = self._ws
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                raw_data = msg.data.strip()
                json_objects = []
                decoder = json.JSONDecoder()
                idx = 0

                while idx < len(raw_data):
                    while idx < len(raw_data) and raw_data[idx].isspace():
                        idx += 1
                    if idx >= len(raw_data):
                        break
                    try:
                        obj, end_idx = decoder.raw_decode(raw_data, idx)
                        json_objects.append(obj)
                        idx = end_idx  # ← = statt +=
                    except json.JSONDecodeError as exc:
                        _LOGGER.warning("WS JSON error: %s", exc)
                        break

                for data in json_objects:
                    rid = data.get("id")
                    # ... Rest bleibt gleich