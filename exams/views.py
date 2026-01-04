from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Exam
from .forms import ExamForm


def exam_list(request):
    q = request.GET.get('q','').strip()
    qs = Exam.objects.select_related('course','classroom').all().order_by('date')
    if q:
        qs = qs.filter(Q(name__icontains=q)|Q(course__name__icontains=q))
    # 移除分页，返回所有数据
    exams = qs
    return render(request, 'exams/list.html', {'exams': exams, 'q': q})


def exam_add(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('exam_list')
    else:
        form = ExamForm()
    return render(request, 'exams/form.html', {'form': form, 'title': '新增考试'})


def exam_edit(request, id):
    obj = get_object_or_404(Exam, pk=id)
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('exam_list')
    else:
        form = ExamForm(instance=obj)
    return render(request, 'exams/form.html', {'form': form, 'title': '编辑考试'})


def exam_delete(request, id):
    obj = get_object_or_404(Exam, pk=id)
    if request.method == 'POST':
        obj.delete()
        return redirect('exam_list')
    return render(request, 'exams/delete.html', {'obj': obj})
