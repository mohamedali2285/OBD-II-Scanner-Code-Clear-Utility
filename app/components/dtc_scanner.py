import reflex as rx
from app.state import OBDState


def dtc_code_card(dtc: rx.Var[dict]) -> rx.Component:
    return rx.el.div(
        rx.el.p(dtc["code"], class_name="font-mono font-bold text-purple-700 text-lg"),
        rx.el.p(dtc["description"], class_name="text-gray-600 text-sm"),
        class_name="p-4 bg-gray-50 rounded-lg border border-gray-200",
    )


def clear_codes_dialog() -> rx.Component:
    return rx.cond(
        OBDState.show_clear_dialog,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Confirm Clear Codes",
                        class_name="text-xl font-bold text-gray-800 mb-4",
                    ),
                    rx.el.div(
                        rx.icon(
                            "flag_triangle_right",
                            class_name="text-red-500 mr-3",
                            size=32,
                        ),
                        rx.el.div(
                            rx.el.p(
                                "WARNING: This will clear all Diagnostic Trouble Codes from the vehicle's ECU.",
                                class_name="font-semibold text-red-700",
                            ),
                            rx.el.p(
                                "Do NOT perform this action while driving. Clearing codes can affect emissions test history.",
                                class_name="text-sm text-gray-600 mt-1",
                            ),
                        ),
                        class_name="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg mb-4",
                    ),
                    rx.el.p(
                        "To confirm, please type ",
                        rx.el.span('"CLEAR-YES"', class_name="font-mono font-bold"),
                        " into the box below.",
                        class_name="text-sm text-gray-700 mb-2",
                    ),
                    rx.el.input(
                        placeholder="CLEAR-YES",
                        on_change=OBDState.set_clear_confirmation_input,
                        class_name="w-full p-2 border border-gray-300 rounded-md font-mono mb-4",
                        default_value=OBDState.clear_confirmation_input,
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            on_click=OBDState.toggle_clear_dialog,
                            class_name="px-4 py-2 bg-gray-200 text-gray-800 rounded-md mr-2 hover:bg-gray-300",
                        ),
                        rx.el.button(
                            rx.cond(
                                OBDState.is_clearing_codes,
                                "Clearing...",
                                "Confirm & Clear",
                            ),
                            on_click=OBDState.clear_dtcs,
                            disabled=~OBDState.clear_confirmation_valid
                            | OBDState.is_clearing_codes,
                            class_name="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed",
                        ),
                        class_name="flex justify-end",
                    ),
                    class_name="p-6 bg-white rounded-lg shadow-xl w-full max-w-lg",
                ),
                class_name="fixed inset-0 z-50 flex items-center justify-center p-4",
            ),
            rx.el.div(class_name="fixed inset-0 bg-black/50 z-40"),
        ),
        rx.fragment(),
    )


def dtc_scanner() -> rx.Component:
    return rx.el.div(
        clear_codes_dialog(),
        rx.el.div(
            rx.el.h2(
                "Diagnostic Trouble Codes (DTC)",
                class_name="text-2xl font-bold text-gray-800",
            ),
            rx.el.div(
                rx.el.button(
                    rx.cond(OBDState.is_scanning_dtcs, "Scanning...", "Scan Codes"),
                    on_click=OBDState.scan_dtcs,
                    disabled=~OBDState.is_connected | OBDState.is_scanning_dtcs,
                    class_name="bg-purple-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 shadow-md transition-all duration-300",
                ),
                rx.el.button(
                    "Clear Codes",
                    on_click=OBDState.toggle_clear_dialog,
                    disabled=~OBDState.is_connected
                    | (OBDState.dtc_codes.length() == 0),
                    class_name="bg-red-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-red-700 disabled:bg-gray-400 shadow-md transition-all duration-300",
                ),
                class_name="flex gap-4",
            ),
            class_name="flex justify-between items-center mb-4",
        ),
        rx.el.div(
            rx.cond(
                OBDState.is_scanning_dtcs,
                rx.el.div(
                    rx.spinner(class_name="text-purple-600"),
                    rx.el.p("Scanning...", class_name="ml-2 text-gray-500"),
                    class_name="flex items-center justify-center h-32",
                ),
                rx.cond(
                    OBDState.dtc_codes.length() > 0,
                    rx.el.div(
                        rx.foreach(OBDState.dtc_codes, dtc_code_card),
                        class_name="grid grid-cols-1 md:grid-cols-2 gap-4",
                    ),
                    rx.el.div(
                        rx.icon("square_m", class_name="text-green-500 mb-2", size=48),
                        rx.el.p(
                            "No trouble codes found.",
                            class_name="text-gray-600 font-medium",
                        ),
                        class_name="flex flex-col items-center justify-center h-32 bg-green-50 rounded-lg border border-green-200",
                    ),
                ),
            ),
            class_name="min-h-[10rem]",
        ),
        class_name="p-6 bg-white rounded-xl shadow-lg border border-gray-200 mt-6",
    )