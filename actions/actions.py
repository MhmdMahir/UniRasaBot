from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# Example dataset (replace with your JSONL later)
COURSE_DB = {
    "computer science": "Degree",
    "information technology": "Diploma",
    "business": "Degree"
}

class ActionGetCourseInfo(Action):

    def name(self) -> Text:
        return "action_get_course_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.get_slot("course")

        if course:
            course_lower = course.lower()

            if course_lower in COURSE_DB:
                programme = COURSE_DB[course_lower]
                dispatcher.utter_message(
                    text=f"{course.title()} is offered as a {programme} programme."
                )
            else:
                dispatcher.utter_message(
                    text="Sorry, I couldn't find that course."
                )
        else:
            dispatcher.utter_message(
                text="Please specify a course."
            )

        return []