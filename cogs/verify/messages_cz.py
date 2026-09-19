from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    verify_brief = "Ověření studenta pro přístup na server."
    verify_disabled = "Ověření je v tuto chvíli vypnuté. Prosím, kontaktuj někoho z (Sub)Mod týmu."
    verify_login_parameter = "Přihlašovací FIT login (`xlogin00`), osobní 6místné VUT číslo"
    verify_login_parameter_muni = "UČO"
    verify_already_verified = "{user} Už jsi byl verifikován " \
                              "({admin} pls)."
    verify_send_dumbshit = "{user} Tvůj login. {emote}"
    verify_send_success = "Kód byl odeslán na tvůj mail (`{mail}`). " \
                          "Pokud kód do 10 minut nedorazí, tak si jej nech znovu zaslat. " \
                          "Hledej zprávu s předmětem `{subject}` (může být i ve SPAMu). " \
                          "Pokud tvůj mail není správný, vyber z možností alternativních mailů."
    verify_resend_success = "Kód byl znovuodeslán na tvůj mail (`{mail}`). " \
                          "Pokud kód do 10 minut nedorazí, tak tagni někoho z Mod týmu. " \
                          "Hledej zprávu s předmětem `{subject}` (může být i ve SPAMu). " \
                          "Pokud tvůj mail není správný, vyber z možností alternativních mailů."
    verify_verify_manual = "Čau {user}, nechám {admin}, aby to udělal manuálně, " \
                           "jsi shady (Year: {year})"
    verify_verify_success = "{user} Gratuluji, byl jsi verifikován!"
    verify_post_verify_info = "Role si přidáš v Channels & Roles " \
                              "(Jak na to 👉 https://discord.com/channels/461541385204400138/489461089432633346/635184378065977354)\n" \
                              "Dále se mrkni do <#489461089432633346> pro pravidla a další info"
    server_link = "https://discord.com/channels/461541385204400138/"
    verify_verify_success_mail = "Gratuluji, byl jsi verifikován!"
    verify_post_verify_info_mail = "Podívej se do kanálu " \
                              f"#server-info pro pravidla a další info ({server_link}489461089432633346)"
    verify_mail_content = "Obdržel/a jsi kód pro ověření se k přístup na server VUT FIT.\n" \
                          "Po stisknutí na tlačítko \"Zadat kód\" vyplň ověřovací kód přesně tak jak je uveden níže.\n\n" \
                          "Ověřovací kód: {code}"
    verify_mail_content_html = """
<html>
  <body style="margin:0;padding:0;background-color:#f4f6fb;font-family:Arial,sans-serif;color:#1f2937;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #d8deef;">
            <tr>
              <td style="padding:24px;background:linear-gradient(135deg,#4f46e5,#3730a3);text-align:center;">
                <img src="cid:rubbergod_icon" alt="Rubbergod" width="72" height="72" style="display:block;margin:0 auto 10px auto;border-radius:12px;background:#ffffff;padding:8px;" />
                <h1 style="margin:0;color:#ffffff;font-size:24px;">FIT Discord verifikace</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 30px 20px 30px;">
                <p style="margin:0 0 14px 0;line-height:1.55;">Ahoj! Obdržel/a jsi kód pro ověření přístupu na server VUT FIT.</p>
                <p style="margin:0 0 20px 0;line-height:1.55;">Po stisknutí tlačítka <strong>Zadat kód</strong> vyplň ověřovací kód přesně tak, jak je uveden níže:</p>
                <div style="margin:0 auto 22px auto;padding:14px 20px;max-width:240px;text-align:center;border-radius:10px;background:#eef2ff;border:1px dashed #4f46e5;font-size:32px;letter-spacing:6px;font-weight:700;color:#312e81;">
                  {code}
                </div>
                <p style="margin:0;line-height:1.55;font-size:14px;color:#4b5563;">Pokud ti e-mail přišel neočekávaně, můžeš ho ignorovat.</p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 30px;background:#f9fafc;border-top:1px solid #e5e7eb;text-align:center;">
                <img src="{fit_logo_url}" alt="VUT FIT" width="190" style="display:block;margin:0 auto 10px auto;max-width:100%;height:auto;" />
                <p style="margin:0;font-size:12px;color:#6b7280;">Tato zpráva byla vytvořena automaticky botem Rubbergod.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    verify_verify_not_found = "{user} Login nenalezen nebo jsi neprošel krokem `/verify`. Přečti si prosím <#591386755547136020>. ({admin} pls)."
    verify_verify_wrong_code = "Špatný kód."
    verify_step_done = "{user} Tímto krokem jsi už prošel. ({admin} pls)"
    verify_invalid_channel = "Tento příkaz je možné spustit pouze v DMs nebo na VUT FIT serveru."
    mail_alternative = "Alternativní maily"
    mail_changed = "Změna mailu"
    mail_changed_desc = "Uživatel {login} změnil mail z `{old}` na `{new}`."
    invalid_login = "{user} Neplatný login. Přečti si prosím <#591386755547136020>. ({admin} pls)"
    verify_subject = "FIT Discord verifikace"
    dynamic_verify_requested = "Byla zaslána žádost o verifikaci. Vyčkej prosím než ji někdo z oprávněných osob schválí."
    dynamic_verify_declined = "Tvá žádost o verifikaci byla zamítnuta."
    dynamic_verify_create_brief = "Vytvoření pravidla pro verifikaci"
    dynamic_verify_edit_brief = "Upravení pravidla pro verifikaci"
    dynamic_verify_list_brief = "Zobrazení pravidel pro verifikaci"
    dynamic_verify_rule_id = "Pravidlo k editaci"
    dynamic_verify_edit_success = "Pravidlo bylo úspěšně upraveno."
    dynamic_verify_create_success = "Pravidlo bylo úspěšně vytvořeno."
    dynamic_verify_remove_brief = "Odstranění pravidla pro verifikaci"
    dynamic_verify_remove_success = "Pravidlo bylo úspěšně odstraněno."
    dynamic_verify_rule_missing = "Nebylo zadáno platné ID pravidla."
    dynamic_verify_rule_exists = "ID s tímto pravidlem již existuje."
    dynamic_verify_invalid_state = "Nepovolený stav. Lze zadat pouze True/False"
    dynamic_verify_role_not_exists = "Role `{role}` neexistuje."
    dynamic_verify_no_roles = "Nebyla nalezena žádná role."
    dynamic_verify_missing_rule = "Toto pravidlo (`{rule_id}`) neexistuje."
