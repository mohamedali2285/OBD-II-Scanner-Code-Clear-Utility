import reflex as rx
from typing import TypedDict
import asyncio
import obd
import serial.tools.list_ports
from serial.serialutil import SerialException
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)


class DTC(TypedDict):
    code: str
    description: str


class LiveData(TypedDict):
    name: str
    value: str | int | float
    unit: str


MOCK_DTCS: list[DTC] = [
    {
        "code": "P0420",
        "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
    },
    {"code": "P0301", "description": "Cylinder 1 Misfire Detected"},
    {"code": "P0171", "description": "System Too Lean (Bank 1)"},
]
MOCK_LIVE_DATA: dict[str, LiveData] = {
    "RPM": {"name": "RPM", "value": 850, "unit": "RPM"},
    "SPEED": {"name": "Speed", "value": 0, "unit": "km/h"},
    "COOLANT_TEMP": {"name": "Coolant Temp", "value": 90, "unit": "°C"},
    "ENGINE_LOAD": {"name": "Engine Load", "value": 35.5, "unit": "%"},
    "FUEL_STATUS": {"name": "Fuel Status", "value": "Closed Loop", "unit": ""},
}


class OBDState(rx.State):
    connection_status: str = "NOT_CONNECTED"
    available_ports: list[str] = []
    selected_port: str = ""
    connection_error: str = ""
    vin: str = ""
    is_scanning_ports: bool = False
    dtc_codes: list[DTC] = []
    is_scanning_dtcs: bool = False
    show_clear_dialog: bool = False
    clear_confirmation_input: str = ""
    is_clearing_codes: bool = False
    live_data: dict[str, LiveData] = {}
    is_watching_live: bool = False
    session_log: list[str] = []
    _connection: obd.Async | None = None
    _use_mock_data: bool = False

    @rx.var
    def is_connected(self) -> bool:
        return self.connection_status == "CONNECTED"

    @rx.var
    def clear_confirmation_valid(self) -> bool:
        return self.clear_confirmation_input == "CLEAR-YES"

    def _log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.session_log.append(f"[{timestamp}] {message}")

    @rx.event(background=True)
    async def scan_for_ports(self):
        async with self:
            self.is_scanning_ports = True
            self.available_ports.clear()
            self._log_message("Scanning for available serial ports...")
        try:
            ports = await asyncio.to_thread(serial.tools.list_ports.comports)
            port_devices = [port.device for port in ports]
            async with self:
                self.available_ports = port_devices
                if port_devices:
                    self.selected_port = port_devices[0]
                    self._log_message(f"Found ports: {', '.join(port_devices)}")
                else:
                    self._log_message("No serial ports found.")
                self.is_scanning_ports = False
        except Exception as e:
            logging.exception(e)
            async with self:
                self.connection_error = f"Error scanning ports: {e}"
                self._log_message(f"ERROR: {self.connection_error}")
                self.is_scanning_ports = False

    @rx.event(background=True)
    async def connect_to_adapter(self):
        async with self:
            if self.is_connected:
                return
            self.connection_status = "CONNECTING"
            self.connection_error = ""
            self._log_message(f"Attempting to connect to {self.selected_port}...")
        if not self.selected_port:
            async with self:
                self.connection_status = "ERROR"
                self.connection_error = "No port selected."
                self._log_message("ERROR: No port selected.")
            return
        if self._use_mock_data:
            await asyncio.sleep(2)
            async with self:
                self.connection_status = "CONNECTED"
                self.vin = "MOCK_VIN_123456789"
                self._log_message("Connected in mock mode.")
                self.live_data = MOCK_LIVE_DATA
            return
        try:
            connection = await asyncio.to_thread(obd.Async, self.selected_port)
            async with self:
                self._connection = connection
            await asyncio.to_thread(self._connection.watch, obd.commands.RPM)
            await asyncio.to_thread(self._connection.start)
            await asyncio.sleep(3)
            if self._connection.status() == obd.OBDStatus.CAR_CONNECTED:
                vin_cmd = await self._connection.query(obd.commands.VIN)
                async with self:
                    self.connection_status = "CONNECTED"
                    self.vin = vin_cmd.value if not vin_cmd.is_null else "N/A"
                    self._log_message(
                        f"Successfully connected to vehicle. VIN: {self.vin}"
                    )
            else:
                raise Exception(
                    f"Connection failed. Status: {self._connection.status()}"
                )
        except SerialException as e:
            logging.exception(e)
            async with self:
                self.connection_status = "ERROR"
                self.connection_error = f"Serial Port Error: {e}. Ensure adapter is connected and port is correct."
                self._log_message(f"ERROR: {self.connection_error}")
            if self._connection:
                await asyncio.to_thread(self._connection.close)
            async with self:
                self._connection = None
        except Exception as e:
            logging.exception(e)
            async with self:
                self.connection_status = "ERROR"
                self.connection_error = str(e)
                self._log_message(f"ERROR: {self.connection_error}")
            if self._connection:
                await asyncio.to_thread(self._connection.close)
            async with self:
                self._connection = None

    @rx.event(background=True)
    async def disconnect_adapter(self):
        async with self:
            self._log_message("Disconnecting...")
            self.is_watching_live = False
        if self._connection:
            await asyncio.to_thread(self._connection.stop)
            await asyncio.to_thread(self._connection.close)
        async with self:
            self._connection = None
            self.connection_status = "NOT_CONNECTED"
            self.vin = ""
            self.dtc_codes.clear()
            self.live_data.clear()
            self._log_message("Disconnected.")

    @rx.event(background=True)
    async def scan_dtcs(self):
        async with self:
            self.is_scanning_dtcs = True
            self.dtc_codes.clear()
            self._log_message("Scanning for Diagnostic Trouble Codes (DTCs)...")
        if self._use_mock_data:
            await asyncio.sleep(1.5)
            async with self:
                self.dtc_codes = MOCK_DTCS
                self._log_message(f"Found {len(MOCK_DTCS)} mock DTCs.")
                self.is_scanning_dtcs = False
            return
        if self.is_connected and self._connection:
            try:
                response = await self._connection.query(obd.commands.GET_DTC)
                if not response.is_null:
                    dtcs = []
                    for code_tuple in response.value:
                        dtcs.append(
                            {"code": code_tuple[0], "description": code_tuple[1]}
                        )
                    async with self:
                        self.dtc_codes = dtcs
                        self._log_message(f"Found {len(dtcs)} DTCs.")
                else:
                    async with self:
                        self._log_message("No DTCs found.")
            except Exception as e:
                logging.exception(e)
                async with self:
                    self._log_message(f"Error reading DTCs: {e}")
            finally:
                async with self:
                    self.is_scanning_dtcs = False
        else:
            async with self:
                self._log_message("Cannot scan DTCs: Not connected.")
                self.is_scanning_dtcs = False

    @rx.event
    def toggle_clear_dialog(self):
        self.show_clear_dialog = not self.show_clear_dialog
        self.clear_confirmation_input = ""

    @rx.event(background=True)
    async def clear_dtcs(self):
        async with self:
            if not self.clear_confirmation_valid:
                yield rx.toast("Invalid confirmation text.", duration=3000)
                return
            self.is_clearing_codes = True
            self._log_message("Attempting to clear DTCs...")
        if self._use_mock_data:
            await asyncio.sleep(2)
            async with self:
                self.dtc_codes.clear()
                self._log_message("Mock DTCs cleared.")
                self.is_clearing_codes = False
                self.show_clear_dialog = False
            yield rx.toast("Codes Cleared (Mock Mode)", duration=3000)
            return
        if self.is_connected and self._connection:
            try:
                response = await self._connection.query(obd.commands.CLEAR_DTC)
                if not response.is_null and response.value:
                    async with self:
                        self.dtc_codes.clear()
                        self._log_message("CLEAR_DTC command successful.")
                    yield rx.toast("Diagnostic Trouble Codes Cleared", duration=3000)
                else:
                    async with self:
                        self._log_message(
                            f"CLEAR_DTC command failed. Response: {response.value}"
                        )
                    yield rx.toast("Failed to clear codes.", duration=3000)
            except Exception as e:
                logging.exception(e)
                async with self:
                    self._log_message(f"Error clearing DTCs: {e}")
                yield rx.toast(f"Error: {e}", duration=3000)
            finally:
                async with self:
                    self.is_clearing_codes = False
                    self.show_clear_dialog = False
        else:
            async with self:
                self._log_message("Cannot clear DTCs: Not connected.")
                self.is_clearing_codes = False

    def _update_live_data(self, response):
        if not response.is_null:
            key = response.command.name
            asyncio.run(self.async_update_live_data(key, response))

    @rx.event
    async def async_update_live_data(self, key, response):
        self.live_data[key] = {
            "name": response.command.name.replace("_", " ").title(),
            "value": response.value.magnitude
            if hasattr(response.value, "magnitude")
            else response.value,
            "unit": str(response.value.units)
            if hasattr(response.value, "units")
            else "",
        }

    @rx.event(background=True)
    async def toggle_live_watch(self):
        if self._use_mock_data:
            async with self:
                self.is_watching_live = not self.is_watching_live
                status = "Started" if self.is_watching_live else "Stopped"
                self._log_message(f"{status} live data watch (Mock).")
            return
        if not self.is_connected or not self._connection:
            yield rx.toast("Not connected to vehicle.", duration=3000)
            return
        if self.is_watching_live:
            await asyncio.to_thread(self._connection.unwatch_all)
            async with self:
                self.is_watching_live = False
                self._log_message("Stopped watching live data.")
        else:
            async with self:
                self.is_watching_live = True
                self._log_message("Started watching live data.")
            supported_live_pids = [
                obd.commands.RPM,
                obd.commands.SPEED,
                obd.commands.COOLANT_TEMP,
                obd.commands.ENGINE_LOAD,
                obd.commands.FUEL_STATUS,
            ]
            for cmd in supported_live_pids:
                await asyncio.to_thread(
                    self._connection.watch, cmd, callback=self._update_live_data
                )