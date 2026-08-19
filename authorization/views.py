from django.shortcuts import render

# Create your views here.

# ==== FAQ (Часто задаваемые вопросы) ====

@login_required
@require_http_methods(["GET"])
def faq_view(request: HttpRequest) -> HttpResponse:
    """
    Rule-based FAQ screen. The user picks a question (no free text); the
    answer is rendered on the same page. Two questions in Phase 1:

    1. Access rights - dynamic: lists the screens this user can reach,
       resolved from accessible_screens (context processor) against the
       Screen catalogue (code -> Russian name).
    2. Platform purpose - static explanatory text.
    """
    from django.shortcuts import render

    from authorization.models import Screen

    # 1) Kullanicinin erisebildigi ekranlar (context processor ile ayni kaynak)
    from authorization.context_processors import accessible_screens as _acc
    codes = _acc(request).get("accessible_screens", set())

    # Kod -> Rusca isim eslemesi (Screen katalogu), sadece erisebildikleri
    name_by_code = dict(Screen.objects.values_list("code", "name"))
    my_screens = [name_by_code.get(code, code) for code in codes if code in name_by_code]
    my_screens = sorted(set(my_screens))

    context = {
        "my_screens": my_screens,
        "user_display": request.user.get_full_name() or request.user.username,
    }
    return render(request, "authorization/faq.html", context)
