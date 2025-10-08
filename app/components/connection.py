import reflex as rx
from app.state import OBDState


def connection_manager() -> rx.Component:
    return rx.el.div(
        rx.el.h2("Connection", class_name="text-2xl font-bold text-gray-800 mb-4"),
        rx.el.div(
            rx.el.div(
                rx.el.p("Status:", class_name="font-semibold mr-2"),
                rx.el.span(
                    OBDState.connection_status,
                    class_name=rx.cond(
                        OBDState.is_connected,
                        "text-green-600 font-bold",
                        "text-amber-600 font-bold",
                    ),
                ),
                class_name="flex items-center text-lg mb-2",
            ),
            rx.cond(
                OBDState.is_connected,
                rx.el.p(
                    f"VIN: {OBDState.vin}", class_name="text-sm text-gray-500 font-mono"
                ),
                rx.el.p(OBDState.connection_error, class_name="text-sm text-red-500"),
            ),
            class_name="mb-4 p-4 bg-gray-50 rounded-lg border",
        ),
        rx.cond(
            ~OBDState.is_connected,
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Select Port",
                        class_name="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    rx.el.div(
                        rx.el.select(
                            rx.foreach(
                                OBDState.available_ports,
                                lambda port: rx.el.option(port, value=port),
                            ),
                            value=OBDState.selected_port,
                            on_change=OBDState.set_selected_port,
                            placeholder="Select a port...",
                            class_name="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm rounded-md shadow-sm",
                        ),
                        rx.el.button(
                            rx.icon("refresh-cw", size=16),
                            on_click=OBDState.scan_for_ports,
                            is_loading=OBDState.is_scanning_ports,
                            class_name="p-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 ml-2",
                        ),
                        class_name="flex items-center",
                    ),
                    class_name="mb-4",
                ),
                rx.el.button(
                    "Connect",
                    on_click=OBDState.connect_to_adapter,
                    is_loading=OBDState.connection_status == "CONNECTING",
                    class_name="w-full bg-purple-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-purple-700 shadow-md elevation-3 transition-all duration-300",
                ),
            ),
            rx.el.button(
                "Disconnect",
                on_click=OBDState.disconnect_adapter,
                class_name="w-full bg-red-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-red-700 shadow-md elevation-3 transition-all duration-300",
            ),
        ),
        class_name="p-6 bg-white rounded-xl shadow-lg border border-gray-200",
    )