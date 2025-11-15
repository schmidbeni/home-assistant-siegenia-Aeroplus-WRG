from __future__ import annotations

from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DATA_COORDINATOR

UNIT_MAP = {
    "airbase.humidity.indoor": "%",
    "airbase.humidity.outdoor": "%",
    "airbase.temperature.indoor": "°C",
    "airbase.temperature.outdoor": "°C",
    "co2_value": "ppm",
    "fanmode": None,
    "maxfanpower": None,
    "systemname": None,
    "connection": None,
    "airquality": None,
    "maxfanpowermanual": None,
}

def _flatten(data: Dict[str, Any], parent: str = "", out: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if out is None:
        out = {}
    for k, v in (data or {}).items():
        key = f"{parent}.{k}" if parent else str(k)
        if isinstance(v, dict):
            _flatten(v, key, out)
        else:
            out[key] = v
    return out

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]

    combined = {}
    for part in ("state", "params", "info"):
        d = (coordinator.data or {}).get(part) or {}
        if isinstance(d, dict):
            combined.update(d)
    flat = _flatten(combined)
    flat.update(combined)

    entities: list[SensorEntity] = []
    for key, unit in UNIT_MAP.items():
        if key in flat:
            entities.append(SiegeniaKeySensor(coordinator, entry, key, unit))

    #entities.append(SiegeniaRawStateSensor(coordinator, entry))
    async_add_entities(entities)

class SiegeniaKeySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, key: str, unit: str | None) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        # Get system name from device info
        system_name = self._get_system_name()
        name = key.replace("_", " ").replace(".", " ").title()
        self._attr_name = f"{system_name} {name}" if system_name else f"Siegenia {name}"
        slug = key.lower().replace(" ", "-").replace(".", "-").replace("_", "-")
        self._attr_unique_id = f"{entry.entry_id}-{slug}"
        if unit:
            self._attr_native_unit_of_measurement = unit
    
    @property
    def device_info(self):
        """Return device information to link this entity with the device."""
        system_name = self._get_system_name()
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": system_name if system_name else "Siegenia Airoplus",
            "manufacturer": "Siegenia",
            "model": "Airoplus WRG Smart",
        }
            
    def _get_system_name(self) -> str | None:
        """Get the system name from device info."""
        data = self.coordinator.data or {}
        for part in ("state", "params", "info"):
            d = data.get(part) or {}
            if isinstance(d, dict):
                system_name = d.get("systemname") or d.get("device_name")
                if system_name:
                    return system_name
        return None

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        combined = {}
        for part in ("state", "params", "info"):
            d = data.get(part) or {}
            if isinstance(d, dict):
                combined.update(d)
        flat = combined.copy()
        def _flatten_in(x: dict, parent: str = "", out: dict | None = None):
            if out is None:
                out = {}
            for k, v in (x or {}).items():
                kk = f"{parent}.{k}" if parent else str(k)
                if isinstance(v, dict):
                    _flatten_in(v, kk, out)
                else:
                    out[kk] = v
            return out
        flat.update(_flatten_in(combined))
        return flat.get(self._key)

class SiegeniaRawStateSensor(CoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:code-json"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        system_name = self._get_system_name()
        self._attr_name = f"{system_name} Raw State" if system_name else "Siegenia Raw State"
        self._attr_unique_id = f"{entry.entry_id}-raw-state"
    
    @property
    def device_info(self):
        """Return device information to link this entity with the device."""
        system_name = self._get_system_name()
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": system_name if system_name else "Siegenia Airoplus",
            "manufacturer": "Siegenia",
            "model": "Airoplus WRG Smart",
        }
        
    def _get_system_name(self) -> str | None:
        """Get the system name from device info."""
        data = self.coordinator.data or {}
        for part in ("state", "params", "info"):
            d = data.get(part) or {}
            if isinstance(d, dict):
                system_name = d.get("systemname") or d.get("device_name")
                if system_name:
                    return system_name
        return None

    @property
    def native_value(self) -> str:
        from json import dumps
        data = self.coordinator.data or {}
        combined = {}
        for part in ("state", "params", "info"):
            d = data.get(part) or {}
            if isinstance(d, dict):
                combined.update(d)
        return dumps(combined, ensure_ascii=False)