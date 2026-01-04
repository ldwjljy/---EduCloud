from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from .models import Teacher
from .forms import TeacherForm


def teacher_list(request):
    q = request.GET.get('q','').strip()
    qs = Teacher.objects.all().order_by('name')
    if q:
        qs = qs.filter(Q(name__icontains=q)|Q(department__icontains=q)|Q(title__icontains=q))
    # 移除分页，返回所有数据
    teachers = qs
    return render(request, 'teachers/list.html', {'teachers': teachers, 'q': q})


def teacher_add(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teacher_list')
    else:
        form = TeacherForm()
    return render(request, 'teachers/form.html', {'form': form, 'title': '新增教师'})


def teacher_edit(request, id):
    obj = get_object_or_404(Teacher, pk=id)
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('teacher_list')
    else:
        form = TeacherForm(instance=obj)
    return render(request, 'teachers/form.html', {'form': form, 'title': '编辑教师'})


def teacher_delete(request, id):
    obj = get_object_or_404(Teacher, pk=id)
    if request.method == 'POST':
        obj.delete()
        return redirect('teacher_list')
    return render(request, 'teachers/delete.html', {'obj': obj})
