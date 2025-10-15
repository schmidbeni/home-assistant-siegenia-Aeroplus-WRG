# Siegenia for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

A Home Assistant integration to control and monitor Siegenia Aeroplus WRG smart ventilation devices with Co2 sensor.
Vibe coded, based on the awesome work for iobroker here: https://github.com/Apollon77/ioBroker.siegenia 

## Features

### Core Features
- Local control via WebSocket connection (no cloud dependency)
- Real-time updates through push notifications + polling (10s interval)
- SSL support with configurable port (default: 443)

### Available Entities

#### Fan Control
- **Siegenia Fan**: Control fan power and on/off state
  - Supports percentage-based control (0-100%)
  - 100% maps to device's maximum airflow capacity
  - Respects manual airflow cap settings
  - Features: Turn On/Off, Set Speed/Percentage

#### Numeric Control
- **Siegenia Fan Power**: Direct airflow control in m³/h
  - Auto-adjusts to device's maximum capacity
  - Takes into account manual power limitations

#### Mode Control
- **Siegenia Auto Mode** (Switch): Toggle automatic operation mode

#### Sensors
- Temperature (Indoor/Outdoor) in °C
- Humidity (Indoor/Outdoor) in %
- CO₂ Level (ppm)
- Air Quality
- Maximum Fan Power
- Manual Fan Power Cap
- System Name
- Connection Status
- **Siegenia Online** (Binary Sensor): WebSocket connection status
- **Siegenia Raw State**: Diagnostic sensor showing complete device state

## Installation

### HACS Installation (Recommended)
1. Ensure [HACS](https://hacs.xyz/) is installed
2. Add this repository to HACS
3. Search for "Siegenia" in HACS integrations
4. Install the integration
5. Restart Home Assistant

### Manual Installation
1. Copy the `custom_components/siegenia` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Configuration via UI
1. Go to Settings -> Devices & Services
2. Click "Add Integration"
3. Search for "Siegenia"
4. Enter your device details:
   - Host/IP address
   - Username
   - Password
   - Port (optional, default: 443)
   - SSL (optional, default: enabled)

### Configuration Parameters
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| host | Yes | - | IP address or hostname of your Siegenia device |
| username | Yes | - | Username for device authentication |
| password | Yes | - | Password for device authentication |
| port | No | 443 | WebSocket port |
| use_ssl | No | true | Enable/disable SSL for connection |

## Technical Details

### Connection
- Uses WebSocket for real-time communication
- Maintains persistent connection with heartbeat (10s interval)
- Automatic reconnection on connection loss
- SSL support with self-signed certificate handling

### Update Methods
- Push updates through WebSocket for immediate state changes
- Polling every 10 seconds as fallback
- Coordinator pattern for efficient state management

### Device Control
- Direct parameter control via WebSocket API
- Support for various device parameters and modes
- Automatic state synchronization

## Troubleshooting

### Common Issues
1. **Connection Failures**
   - Verify device IP address and port
   - Check credentials
   - Ensure device is on the same network
   - Verify SSL settings match device configuration

2. **State Updates**
   - Check network connectivity
   - Verify WebSocket connection status via Online sensor
   - Review Home Assistant logs for error messages

### Debugging
- Enable debug logging for more detailed information:
```yaml
logger:
  default: info
  logs:
    custom_components.siegenia: debug
```

## Support

Software is provided as is, if there are issues, solve them yourself, and feel free to push back here to share with the rest.

## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
## Version History

- 0.7.0 (Alpha)
  - Initial public release
  - Basic device control and monitoring
  - Fan, sensor, and auto mode support
  - WebSocket-based local control
