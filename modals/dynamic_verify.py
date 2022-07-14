import disnake
from repository.database.verification import DynamicVerifyRule
from typing import Union
import utils


class DynamicVerifyEditModal(disnake.ui.Modal):
    def __init__(self, guild: disnake.Guild, rule: Union[DynamicVerifyRule, None] = None):
        self.rule = rule

        selected_roles = rule.get_role_ids() if self.is_edit() else []
        guild_roles = list(filter(lambda x: x.name != "@everyone" and x.is_assignable(), guild.roles))
        guild_role_groups = utils.split_to_parts(guild_roles, 25)

        components = [
            disnake.ui.TextInput(
                label="Identifikátor",
                placeholder="Identifikátor",
                custom_id="id",
                style=disnake.TextInputStyle.short,
                required=True,
                value=rule.id if self.is_edit() else None,
            ),
            disnake.ui.TextInput(
                label="Název",
                placeholder="Název",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                required=True,
                value=rule.name if self.is_edit() else None,
            ),
            disnake.ui.Select(
                custom_id="enabled",
                placeholder="Stav",
                options=[
                    disnake.SelectOption(label="Aktivní", value=True, default=True),
                    disnake.SelectOption(label="Neaktivní", value=False),
                ],
            ),
        ]

        if self.is_edit() and not rule.enabled:
            # Change selected value if rule is not enabled. Otherwise keep default values.
            components[2].options[0].default = False
            components[2].options[1].default = True

        for i in range(0, len(guild_role_groups)):
            role_group = guild_role_groups[i]
            components.append(
                disnake.ui.Select(
                    custom_id=f"roles:{i}",
                    placeholder="Výběr rolí",
                    options=[
                        disnake.SelectOption(
                            label=role.name,
                            value=str(role.id),
                            default=role.id in selected_roles,
                            emoji=role.emoji,
                        )
                        for role in role_group
                    ],
                    min_values=0,
                    max_values=min(25, len(guild_roles)),
                )
            )

        super().__init__(
            title="Modifikace verifikačního pravidla"
            if self.is_edit()
            else "Vytvoření verifikačního pravidla",
            custom_id="dynamic_verify_edit",
            timeout=300,
            components=components,
        )

    def is_edit(self):
        return self.rule is not None

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        raise NotImplemented("Dynamic verification modal is not currently supported.") # noqa

        rule_id = str(inter.text_values["id"]).strip() # noqa
        name = str(inter.text_values["name"]).strip() # noqa
        await inter.response.send_message("Hotovo") # TODO Vhodnější text. # noqa
