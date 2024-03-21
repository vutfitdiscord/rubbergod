from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    send_brief = "Pošle zprávu do kanálu"
    resend_brief = "Přepošle existující zprávu do kanálu"
    edit_brief = "Upraví existující zprávu"
    channel_param = "Kanál, do kterého se má zpráva poslat"
    url_param = "Url zprávy, která se má přeposlat"
    message_sent = "Zpráva byla odeslána do kanálu {channel}"
    message_too_long = "Zpráva přesahuje limit 2000 znaků"
