import csv
import openpyxl
from io import StringIO, BytesIO
from django.contrib.auth.models import User
from django.db import transaction
from .models import UserProfile, StudentProfile, TeacherProfile
from organization.models import Class as SchoolClass, College


class ImportResult:
    def __init__(self):
        self.created = 0
        self.skipped = 0
        self.errors = []


def _get_data_from_request(request):
    if 'file' in request.FILES:
        f = request.FILES['file']
        filename = f.name.lower()
        
        # Check if it's an Excel file
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            try:
                wb = openpyxl.load_workbook(f)
                sheet = wb.active
                rows = list(sheet.values)
                if not rows:
                    return []
                
                headers = rows[0]
                data = []
                for row in rows[1:]:
                    item = {}
                    # 某些情况下，row[i] 可能是 None，str(None) 是 'None'，这不是我们想要的
                    for i, header in enumerate(headers):
                        if header:
                            val = row[i]
                            if val is None:
                                val = ''
                            else:
                                val = str(val).strip()
                            item[str(header).strip()] = val
                    data.append(item)
                return data
            except Exception as e:
                # If openpyxl fails, maybe try to read as CSV if it's not actually binary?
                # But filename says xlsx. Let's assume binary format for now.
                # If needed, we could use pandas but that's a heavy dependency.
                # openpyxl is standard for xlsx.
                raise ValueError(f"Failed to parse Excel file: {e}")
        
        # Assume CSV if not Excel
        try:
            content = f.read().decode('utf-8-sig') # Handle BOM
            reader = csv.DictReader(StringIO(content))
            return list(reader)
        except Exception:
            f.seek(0)
            try:
                content = f.read().decode('gbk') # Try GBK for Chinese systems
                reader = csv.DictReader(StringIO(content))
                return list(reader)
            except Exception as e:
                 raise ValueError(f"Failed to decode CSV file: {e}")

    # Fallback to 'csv' field in body
    csv_text = request.data.get('csv', '')
    if csv_text:
        reader = csv.DictReader(StringIO(csv_text))
        return list(reader)
        
    return []


@transaction.atomic
def import_students(request):
    rows = _get_data_from_request(request)
    result = ImportResult()
    
    for row in rows:
        # Support both English and Chinese headers
        username = (row.get('username') or row.get('姓名') or '').strip()
        student_id = str(row.get('student_id') or row.get('学号') or '').strip()
        # 处理可能的科学计数法或浮点数（如果Excel把学号当数字读取）
        if '.' in student_id:
            try:
                student_id = str(int(float(student_id)))
            except ValueError:
                pass
                
        class_id = str(row.get('class_id') or '').strip()
        class_name = (row.get('class_name') or row.get('班级') or '').strip()
        phone = str(row.get('phone') or row.get('联系方式') or '').strip()
        if phone == 'None': phone = ''
        status = (row.get('status') or row.get('状态') or '在读').strip()
        
        if not username or not student_id:
            result.skipped += 1
            result.errors.append(f'missing username/student_id: {row}')
            continue
            
        if User.objects.filter(username=student_id).exists():
            result.skipped += 1
            continue
            
        try:
            user = User.objects.create(username=student_id)
            user.first_name = username
            user.set_password('123456') # Default password
            user.save()
            
            profile = UserProfile.objects.create(user=user, role='student', phone=phone)
            
            school_class = None
            if class_id and class_id.isdigit():
                try:
                    school_class = SchoolClass.objects.get(id=int(class_id))
                except Exception:
                    pass
            if not school_class and class_name:
                school_class = SchoolClass.objects.filter(name=class_name).first()
                
            StudentProfile.objects.create(
                user_profile=profile, 
                student_id=student_id, 
                school_class=school_class, 
                status=status,
                created_by=getattr(request, 'user', None)
            )
            result.created += 1
        except Exception as e:
            result.errors.append(f"Error creating student {student_id}: {str(e)}")
            result.skipped += 1
            
    return result


@transaction.atomic
def import_teachers(request):
    rows = _get_data_from_request(request)
    result = ImportResult()
    
    for row in rows:
        username = (row.get('username') or row.get('姓名') or '').strip()
        teacher_id = str(row.get('teacher_id') or row.get('工号') or '').strip()
        department_id = str(row.get('department_id') or row.get('专业id') or '').strip()
        department_name = (row.get('department_name') or row.get('专业') or '').strip()
        title = (row.get('title') or row.get('职称') or '').strip()
        phone = str(row.get('phone') or row.get('联系方式') or '').strip()
        if phone == 'None': phone = ''
        
        if not username or not teacher_id:
            result.skipped += 1
            result.errors.append(f'missing username/teacher_id: {row}')
            continue
            
        if User.objects.filter(username=teacher_id).exists():
            result.skipped += 1
            continue
            
        try:
            user = User.objects.create(username=teacher_id)
            user.first_name = username
            user.set_password('123456')
            user.save()
            
            profile = UserProfile.objects.create(user=user, role='teacher', phone=phone)
            
            # 查找专业（department 对应 Major 模型）
            from organization.models import Major
            department = None
            if department_id and department_id.isdigit():
                try:
                    department = Major.objects.get(id=int(department_id))
                except Exception:
                    pass
            if not department and department_name:
                department = Major.objects.filter(name=department_name).first()
                
            TeacherProfile.objects.create(
                user_profile=profile, 
                teacher_id=teacher_id,
                title=title,
                department=department, 
                created_by=getattr(request, 'user', None)
            )
            result.created += 1
        except Exception as e:
            result.errors.append(f"Error creating teacher {teacher_id}: {str(e)}")
            result.skipped += 1
            
    return result
