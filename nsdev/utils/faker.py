from types import SimpleNamespace

from faker import Faker


class FakeInfoGenerator:
    def __init__(self, locale: str = "id_ID"):
        self.fake = Faker(locale)

    def generate(self) -> SimpleNamespace:
        profile = self.fake.profile()
        return SimpleNamespace(
            name=profile.get("name"),
            address=profile.get("address"),
            email=profile.get("mail"),
            job=profile.get("job"),
            company=profile.get("company"),
            phone_number=self.fake.phone_number(),
            birthdate=profile.get("birthdate"),
            website=self.fake.url(),
        )
