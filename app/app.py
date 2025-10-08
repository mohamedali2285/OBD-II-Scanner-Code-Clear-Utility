import reflex as rx
from app.state import OBDState
from app.components.connection import connection_manager
from app.components.dtc_scanner import dtc_scanner
from app.components.live_data import live_data_viewer
from app.components.logger import logger_panel


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.icon("wrench", size=48, class_name="text-purple-600 mx-auto mb-2"),
                rx.el.h1(
                    "OBD-II Diagnostic Tool",
                    class_name="text-4xl font-extrabold text-center text-gray-800",
                ),
                rx.el.p(
                    "Connect, scan, and clear vehicle trouble codes with ease.",
                    class_name="text-center text-gray-500 mt-2 mb-8",
                ),
                class_name="py-8",
            ),
            rx.el.div(
                rx.el.div(
                    connection_manager(),
                    dtc_scanner(),
                    class_name="flex flex-col gap-6",
                ),
                rx.el.div(
                    live_data_viewer(), logger_panel(), class_name="flex flex-col gap-6"
                ),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
            ),
            class_name="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8",
        ),
        class_name="font-['JetBrains_Mono'] bg-gray-50 min-h-screen",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, on_load=OBDState.scan_for_ports)