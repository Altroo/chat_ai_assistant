from datetime import datetime, timedelta, timezone
import unittest
from chat_ai_assistant.selection_context import ordinal_target_matches, explicit_target_matches


class OrdinalTargetTests(unittest.TestCase):
    now = datetime(2037, 4, 19, 12, tzinfo=timezone.utc)
    aliases = {"project": r"project|projet", "client": r"client|customer"}

    def check(self, text, identifier=1456, state=None, resource="project"):
        if state is None:
            state = {"resource": "project", "ids": [311, 8092, 1456],
                     "expires_at": (self.now + timedelta(minutes=5)).isoformat()}
        return ordinal_target_matches(text, resource, identifier, state, self.now, self.aliases)

    def test_bilingual_ordinals_require_exact_position_not_membership(self):
        for text in ["Update the third project: status Paused.",
                     "Modifie le troisième projet : statut En pause.",
                     "Delete the 3rd result.", "Supprime le 3ème élément."]:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))
                self.assertFalse(self.check(text, identifier=311))

    def test_conflicting_or_different_resource_references_reject(self):
        for text in ["Delete the first project and the third project.",
                     "Update the third customer.",
                     "Update the third project, project ID 311.",
                     "Update the third project and client identifiant 1456."]:
            with self.subTest(text=text): self.assertFalse(self.check(text))
        self.assertTrue(self.check("Update the third project, project ID 1456."))

    def test_quoted_field_values_are_not_targets(self):
        for text in ['Rename project ID 311 to "The third project".',
                     'Renomme le projet ID 311 « Le troisième projet ».',
                     'Set project ID 311 description to “The third customer”.',
                     "Set project ID 311 title to 'The third project'.",
                     'Rename project ID 311 to First project.']:
            with self.subTest(text=text): self.assertIsNone(self.check(text, identifier=311))
        self.assertTrue(self.check('Rename the third project to "The first project".'))

    def test_unrecognized_requests_defer_to_existing_native_target_logic(self):
        for text in [None, "Update project ID 1456.", "Update the current project."]:
            with self.subTest(text=text): self.assertIsNone(self.check(text))

    def test_invalid_expired_and_incomplete_states_reject(self):
        fresh={"resource":"project", "ids":[311,8092,1456],
               "expires_at":(self.now+timedelta(minutes=5)).isoformat()}
        states=[{}, {**fresh,"resource":"client"}, {**fresh,"ids":[311,8092]},
                {**fresh,"ids":[311,1456,1456]}, {**fresh,"ids":[True,8092,1456]},
                {**fresh,"ids":"1456"}, {**fresh,"ids":list(range(1,12))},
                {**fresh,"expires_at":self.now.isoformat()},
                {**fresh,"expires_at":"2037-04-19T12:05:00"},
                {**fresh,"expires_at":None}]
        for state in states:
            with self.subTest(state=state): self.assertFalse(self.check("Update the third project.",state=state))
        self.assertFalse(self.check("Update the third project.",identifier=True))

    def test_offset_expiry_compares_instants(self):
        state={"resource":"project","ids":[311,8092,1456],"expires_at":"2037-04-19T14:05:00+02:00"}
        self.assertTrue(self.check("Update the third project.",state=state))
        state["expires_at"]="2037-04-19T13:00:00+02:00"
        self.assertFalse(self.check("Update the third project.",state=state))

    def test_standalone_and_article_free_command_targets(self):
        for text in ["Delete the third.", "Supprime le troisième.", "Delete third project.",
                     "Modifie troisième projet : statut En pause."]:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))
                self.assertFalse(self.check(text,identifier=311))

    def test_unquoted_replacement_values_are_not_targets(self):
        self.assertIsNone(self.check("Rename project ID 311 to The third project.",identifier=311))
        self.assertTrue(self.check("Change the third project notes to about the first customer."))
        self.assertTrue(self.check("Modifie le troisième projet : nom Le premier client."))
        self.assertTrue(self.check("Renomme le troisième projet en Le premier projet."))

    def test_introductory_words_do_not_hide_target_or_conflict(self):
        for text in ["I want to delete the third project.",
                     "Je veux en fait supprimer le troisième projet.",
                     "Please do this: delete the third project."]:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))
                self.assertFalse(self.check(text,identifier=311))
        self.assertFalse(self.check("Update the third project, project ID : 311."))


class ExplicitTargetTests(unittest.TestCase):
    aliases = {"project": r"project|projet", "client": r"client|customer", "quote": r"devis|quote"}

    def check(self, text, resource="project", identifier=311, bare=()):
        return explicit_target_matches(text, resource, identifier, self.aliases, bare)

    def test_explicit_pair_rejects_different_resource_or_id(self):
        for text in ["Delete project ID 311.", "Supprime le projet identifiant : 311."]:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))
                self.assertFalse(self.check(text, identifier=72))
                self.assertFalse(self.check(text, resource="client"))

    def test_multiple_incompatible_targets_fail_closed(self):
        for text in ["Delete project ID 311 and client ID 72.",
                     "Delete project ID 311 and project ID 72."]:
            with self.subTest(text=text):
                self.assertFalse(self.check(text))
        self.assertTrue(self.check("Delete project ID 311, project identifiant 311."))

    def test_quoted_and_replacement_ids_cannot_become_target(self):
        for text in ['Update project ID 311 notes to "client ID 72 is the reference".',
                     'Update project ID 311 notes to client ID 72.',
                     'Modifie le projet ID 311 : notes client ID 72.',
                     'Rename project ID 311 to client ID 72.',
                     "Rename project ID 311 to 'client ID 72'."]:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))
                self.assertFalse(self.check(text, resource="client", identifier=72))
        self.assertIsNone(self.check('Update the current project notes to client ID 72.'))
        self.assertIsNone(self.check('Update this project notes to "client ID 72".'))

    def test_bare_id_policy_preserves_business_number_distinction(self):
        for text in ["Delete project 311.", "Supprime le projet numéro 311.", "Delete project #311."]:
            with self.subTest(text=text):
                self.assertIsNone(self.check(text))
                self.assertTrue(self.check(text, bare=("project",)))
        for text in ["Delete quote 311.", "Delete quote number 311.", "Delete quote 0311/38."]:
            with self.subTest(text=text):
                self.assertIsNone(self.check(text, resource="quote", bare=("project",)))

    def test_partial_numeric_tokens_do_not_bind(self):
        for text in ["Delete project ID 0311.", "Delete project ID 311/38.",
                     "Delete project ID 311.72.", "Delete project ID 311-38."]:
            with self.subTest(text=text):
                self.assertIsNone(self.check(text))
        self.assertFalse(self.check("Delete project ID 1.", identifier=True))
        self.assertIsNone(self.check(None))

    def test_field_colon_and_assignment_values_are_not_targets(self):
        for field in ["name", "title", "nom", "titre", "ville", "contact", "email"]:
            for separator in [": ", " = ", "="]:
                text=f"Update this project {field}{separator}client ID 72."
                with self.subTest(field=field, separator=separator):
                    self.assertIsNone(self.check(text, resource="client", identifier=72))
        self.assertTrue(self.check("Update project ID 311 name: client ID 72."))
        self.assertTrue(self.check("Modifie le projet ID 311 : nom client ID 72."))

    def test_full_resource_phrase_precedes_nested_alias(self):
        aliases={"invoice":r"facture(?: client)?|invoice", "client":r"client|customer"}
        text="Supprime la facture client ID 311."
        self.assertTrue(explicit_target_matches(text,"invoice",311,aliases))
        self.assertFalse(explicit_target_matches(text,"client",311,aliases))
        self.assertFalse(explicit_target_matches(text+" Et client ID 72.","invoice",311,aliases))
        self.assertFalse(explicit_target_matches("Delete shared ID 311.","one",311,{"one":"shared","two":"shared"}))
