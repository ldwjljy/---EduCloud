from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Student
from .forms import StudentForm


def student_list(request):
    q = request.GET.get('q','').strip()
    status = request.GET.get('status','')
    qs = Student.objects.all().order_by('student_id')
    if q:
        qs = qs.filter(Q(student_id__icontains=q)|Q(name__icontains=q))
    if status:
        qs = qs.filter(status=status)
    # 移除分页，返回所有数据
    students = qs
    return render(request, 'students/list.html', {'students': students, 'q': q, 'status': status, 'selected_status': status})


def student_add(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'students/form.html', {'form': form, 'title': '新增'})


def student_edit(request, id):
    obj = get_object_or_404(Student, pk=id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm(instance=obj)
    return render(request, 'students/form.html', {'form': form, 'title': '编辑'})


def student_delete(request, id):
    obj = get_object_or_404(Student, pk=id)
    if request.method == 'POST':
        obj.delete()
        return redirect('student_list')
    return render(request, 'students/delete.html', {'obj': obj})
