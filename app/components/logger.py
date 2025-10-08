import reflex as rx
from app.state import OBDState


def logger_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3("Session Log", class_name="text-lg font-semibold text-gray-700 mb-2"),
        rx.el.div(
            rx.foreach(
                OBDState.session_log,
                lambda log: rx.el.p(log, class_name="font-mono text-xs text-gray-600"),
            ),
            class_name="h-48 overflow-y-auto bg-gray-900 text-white p-4 rounded-lg border border-gray-700",
        ),
        class_name="p-6 bg-white rounded-xl shadow-lg border border-gray-200 mt-6",
    )