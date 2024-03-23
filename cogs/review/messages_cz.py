from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    review_add_brief = "Přidá recenzi na předmět. Pokud jsi již recenzi na předmět napsal, bude nahrazena novou."
    review_get_brief = "Vypíše recenze na vybraný předmět"
    review_remove_brief = "Odstraní hodnocení"
    review_list_brief = "Vypíše předměty, které si již ohodnotil"
    review_id_brief = "ID recenze, pouze pro administrátory"
    review_grade_brief = "Známku, kterou by jsi dal předmětu od A-F (za organizaci, splnění očekávání, kvalitu výuky ...)"

    wrong_subject = "Nesprávná zkratka předmětu."
    review_added = "Hodnocení předmětu bylo přidáno."
    reviews_reaction_help = "Pokud byla recenze užitečná dejte 👍, jinak 👎.\n" \
                            "Pro odstranění hlasu je možné použit 🛑.\n" \
                            "Použijte reakce ◀️ a ▶️ pro navigaci mezi recenzemi.\n" \
                            "Pro navigaci v textu delších recenzí použijte 🔼 a 🔽.\n"
    review_vote_own = "Nemůžeš hlasovat pro vlastní recenzi"
    review_remove_success = "Hodnocení předmětu bylo odebráno."
    review_not_found = "Hodnocení předmětu nebylo nalezeno."
    review_remove_denied = "{user}, `id` je pouze pro administrátory. Pro smazání použij jen `subject`."
    review_add_denied = "{user}, na přidání hodnocení předmětu nemáš právo."
    review_not_on_server = "{user}, na použití tohoto příkazu musíš být na FITwide serveru."

    # review embed
    embed_description = "{name}\n**Průměrná známka od studenta:** {grade}"
    no_reviews = "*Zatím nic*"
    text_label = "Text recenze"
    text_page_label = "Stránka textu"
    author_label = "Autor"
    grade_label = "Kvalita předmětu"
    date_label = "Datum"
    other_reviews_label = "Další hodnocení"
    authored_list_label = "Ohodnotil jsi:"

    subject_update_biref = "Automaticky vyhledá a přidá předměty do reviews i subject databáze"
    subject_update_overwrite_brief = "Přepíše všechny informace o předmětech. Využít pouze v kombinaci s další aktualizací bez přepisu."
    subject_update_error = "Aktualizace se nezdařila pro <{url}>\n"
    subject_update_success = "Předměty byly aktualizovány."
    shortcut_brief = "Vrací stručné informace o předmětu"
    tierboard_brief = "Založeno na `reviews` z průměru tier hodnot"
    tierboard_missing_year = f"Nemáš ročníkovou roli, prosím specifikuj ročník"
