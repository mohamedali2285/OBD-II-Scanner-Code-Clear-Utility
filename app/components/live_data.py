import reflex as rx
from app.state import OBDState


def live_data_item(item: rx.Var[dict]) -> rx.Component:
    return rx.el.div(
        rx.el.p(item["name"], class_name="text-sm font-medium text-gray-500"),
        rx.el.div(
            rx.el.span(
                item["value"].to_string(),
                class_name="text-3xl font-bold text-purple-700",
            ),
            rx.el.span(item["unit"], class_name="text-sm text-gray-600 ml-1 mt-2"),
            class_name="flex items-end",
        ),
        class_name="p-4 bg-gray-50 rounded-xl border border-gray-200 text-center transform hover:scale-105 transition-transform duration-200",
    )


def live_data_viewer() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2("Live Data", class_name="text-2xl font-bold text-gray-800"),
            rx.el.button(
                rx.cond(OBDState.is_watching_live, "Stop", "Start"),
                " Watch",
                on_click=OBDState.toggle_live_watch,
                disabled=~OBDState.is_connected,
                class_name=rx.cond(
                    OBDState.is_watching_live,
                    "bg-amber-500 text-white font-bold py-2 px-4 rounded-lg hover:bg-amber-600 disabled:bg-gray-400 shadow-md transition-all duration-300",
                    "bg-green-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 shadow-md transition-all duration-300",
                ),
            ),
            class_name="flex justify-between items-center mb-4",
        ),
        rx.cond(
            OBDState.is_connected,
            rx.el.div(
                rx.foreach(OBDState.live_data.values(), live_data_item),
                class_name="grid grid-cols-2 md:grid-cols-3 gap-4",
            ),
            rx.el.div(
                rx.icon("power-off", class_name="text-gray-400 mb-2", size=48),
                rx.el.p(
                    "Connect to vehicle to see live data.",
                    class_name="text-gray-500 font-medium",
                ),
                class_name="flex flex-col items-center justify-center h-48 bg-gray-50 rounded-lg border border-dashed",
            ),
        ),
        class_name="p-6 bg-white rounded-xl shadow-lg border border-gray-200",
    )