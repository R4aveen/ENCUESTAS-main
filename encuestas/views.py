from django.shortcuts import redirect

def home(request):
    if request.user.is_authenticated:
        return render(request, "core/usuarios_lista.html")   
    return redirect("login")                 
