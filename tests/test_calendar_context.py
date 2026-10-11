import json
import unittest
from types import SimpleNamespace
from chat_ai_assistant.calendar_context import with_calendar_context
from chat_ai_assistant.orchestrator import ChatAIOrchestrator


class CalendarContextTests(unittest.TestCase):
    def test_previous_month_crosses_year(self):
        anchors = with_calendar_context({'today': '2035-01-01'})['calendar']
        self.assertEqual(anchors['yesterday'], '2034-12-31')
        self.assertEqual(anchors['previous_month_first_day'], '2034-12-01')
        self.assertEqual(anchors['previous_month_last_day'], '2034-12-31')
        self.assertEqual(anchors['current_year_first_day'], '2035-01-01')
        self.assertEqual(anchors['previous_year_first_day'], '2034-01-01')
        self.assertEqual(anchors['previous_year_last_day'], '2034-12-31')

    def test_february_leap_and_nonleap_year(self):
        for today, expected in [('2028-03-01', '2028-02-29'), ('2029-03-01', '2029-02-28')]:
            with self.subTest(today=today):
                anchors = with_calendar_context({'today': today})['calendar']
                self.assertEqual(anchors['yesterday'], expected)
                self.assertEqual(anchors['previous_month_last_day'], expected)
                self.assertEqual(anchors['current_month_first_day'], today)

    def test_uses_application_date_and_does_not_mutate_input(self):
        context = {'today': '2035-04-09', 'company_id': 7, 'calendar': {'yesterday': '2099-01-01'}}
        result = with_calendar_context(context)
        self.assertEqual(result['calendar']['yesterday'], '2035-04-08')
        self.assertEqual(result['company_id'], 7)
        self.assertEqual(context['calendar']['yesterday'], '2099-01-01')

    def test_absent_or_invalid_date_adds_no_guessed_boundaries(self):
        for value in (None, True, '2035-02-30', '20350409', '0001-01-01', '2035-04-09T23:00:00Z'):
            with self.subTest(value=value):
                self.assertEqual(with_calendar_context({'today': value, 'calendar': {'yesterday': 'forged'}}), {'today': value})

    def test_actual_planner_receives_calendar_but_user_message_is_unchanged(self):
        captured = {}
        class Model:
            def choose(self, messages, tools, cancel):
                captured['messages'] = messages
                return {'tool': 'clarify', 'message': 'Which customer?'}, {}
        executor = SimpleNamespace(authorize=lambda: None, capabilities=lambda: {'read'})
        registry = SimpleNamespace(permitted=lambda caps: [])
        prompt = 'Find delivery notes from the first day of last month through yesterday.'
        ChatAIOrchestrator(Model(), registry, executor).run(prompt, context={'today': '2035-04-09'})
        context = json.loads(captured['messages'][0]['content'].split('Trusted context: ', 1)[1])
        self.assertEqual(context['calendar']['previous_month_first_day'], '2035-03-01')
        self.assertEqual(context['calendar']['yesterday'], '2035-04-08')
        self.assertEqual(captured['messages'][-1]['content'], prompt)


if __name__ == '__main__':
    unittest.main()
