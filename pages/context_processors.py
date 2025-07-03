from company.models import Area

def areas(request):
    areas_qs = Area.objects.all()
    print("Context processor areas count:", areas_qs.count()) 
    return {
        'all_areas': areas_qs
    }
