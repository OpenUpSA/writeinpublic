from global_test_case import GlobalTestCase as TestCase
from instance.models import PopoloPerson, WriteItInstance
from contactos.models import ContactType, Contact


class TestPopoloPerson(TestCase):
    def setUp(self):
        super(TestPopoloPerson, self).setUp()
        self.person = PopoloPerson.objects.get(id=1)
        self.contact_type, created = ContactType.objects.get_or_create(
            name="e-mail", defaults={"label_name": "Electronic Mail"}
        )
        writeitinstance = WriteItInstance.objects.get(id=1)
        self.contact = Contact.objects.create(
            contact_type=self.contact_type,
            value="test@email.com",
            person=self.person,
            writeitinstance=writeitinstance,
        )

    def test_has_contacts(self):
        self.assertIn(self.person, PopoloPerson.objects.has_contacts())
        self.assertNotIn(self.person, PopoloPerson.objects.doesnt_have_contacts())

    def test_doesnt_have_contacts(self):
        self.person.contact_set.all().delete()
        self.assertIn(self.person, PopoloPerson.objects.doesnt_have_contacts())
        self.assertNotIn(self.person, PopoloPerson.objects.has_contacts())
