from company.models import Area

def areas(request):
    return {
        'all_areas': Area.objects.all()
    }
