from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Classroom
from .forms import ClassroomForm


def classroom_list(request):
    q = request.GET.get('q','').strip()
    qs = Classroom.objects.all().order_by('name')
    if q:
        qs = qs.filter(Q(name__icontains=q)|Q(location__icontains=q))
    # 移除分页，返回所有数据
    classrooms = qs
    return render(request, 'classrooms/list.html', {'classrooms': classrooms, 'q': q})


def classroom_add(request):
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('classroom_list')
    else:
        form = ClassroomForm()
    return render(request, 'classrooms/form.html', {'form': form, 'title': '新增教室'})


def classroom_edit(request, id):
    obj = get_object_or_404(Classroom, pk=id)
    if request.method == 'POST':
        form = ClassroomForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('classroom_list')
    else:
        form = ClassroomForm(instance=obj)
    return render(request, 'classrooms/form.html', {'form': form, 'title': '编辑教室'})


def classroom_delete(request, id):
    obj = get_object_or_404(Classroom, pk=id)
    if request.method == 'POST':
        obj.delete()
        return redirect('classroom_list')
    return render(request, 'classrooms/delete.html', {'obj': obj})
