import disnake


class VerifyView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Zadat kód",
        style=disnake.ButtonStyle.success,
        custom_id="verify:set_code",
    )
    async def code_success(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        print("Kod dorazil")


class VerifyWithResendButtonView(VerifyView):
    def __init__(self):
        super().__init__()

    @disnake.ui.button(
        label="Znovu odeslat kód",
        style=disnake.ButtonStyle.danger,
        custom_id="verify:missing_code",
    )
    async def missing_code(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        print("Kód nedorazil")
