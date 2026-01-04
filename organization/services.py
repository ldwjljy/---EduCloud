from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from typing import List, Dict, Any, Optional

from .models import College, Major, Class


class OrganizationService:
    """组织架构业务逻辑服务类"""
    
    def validate_college_deletion(self, college: College) -> None:
        """
        验证学院是否可以删除
        检查是否存在关联的专业
        """
        if college.majors.filter(is_deleted=False).exists():
            raise ValidationError("该学院下存在专业，无法删除")
    
    def validate_major_deletion(self, major: Major) -> None:
        """
        验证专业是否可以删除
        检查是否存在关联的班级
        """
        if major.classes.filter(is_deleted=False).exists():
            raise ValidationError("该专业下存在班级，无法删除")
    
    def validate_class_deletion(self, school_class: Class) -> None:
        """
        验证班级是否可以删除
        检查是否存在关联的教师或学生
        """
        # 检查是否有班主任
        if school_class.head_teacher:
            raise ValidationError("该班级存在班主任，请先解除关联")
        
        # 这里可以添加更多检查，比如是否有学生等
    
    def validate_organization_hierarchy(self, college: College, major: Major, school_class: Class) -> None:
        """
        验证组织架构层级关系
        确保专业属于学院，班级属于专业
        """
        if major.college != college:
            raise ValidationError("专业不属于指定的学院")
        
        if school_class.major != major:
            raise ValidationError("班级不属于指定的专业")
    
    def get_college_tree(self) -> List[Dict[str, Any]]:
        """
        获取学院树形结构
        包含学院、专业和班级的层级关系
        """
        colleges = College.objects.filter(is_deleted=False).prefetch_related(
            'majors', 'majors__classes'
        ).order_by('code')
        
        tree_data = []
        for college in colleges:
            college_data = {
                'id': college.id,
                'code': college.code,
                'name': college.name,
                'type': 'college',
                'children': []
            }
            
            # 获取该学院下的专业
            majors = college.majors.filter(is_deleted=False).order_by('code')
            for major in majors:
                major_data = {
                    'id': major.id,
                    'code': major.code,
                    'name': major.name,
                    'type': 'major',
                    'duration_type': major.duration_type,
                    'duration_label': major.get_duration_label(),
                    'children': []
                }
                
                # 获取该专业下的班级
                classes = major.classes.filter(is_deleted=False).order_by('-enrollment_year', 'class_number')
                for school_class in classes:
                    class_data = {
                        'id': school_class.id,
                        'name': school_class.name,
                        'type': 'class',
                        'enrollment_year': school_class.enrollment_year,
                        'class_number': school_class.class_number,
                        'head_teacher': {
                            'employee_id': school_class.head_teacher.employee_id,
                            'name': school_class.head_teacher.name
                        } if school_class.head_teacher else None
                    }
                    major_data['children'].append(class_data)
                
                college_data['children'].append(major_data)
            
            tree_data.append(college_data)
        
        return tree_data
    
    def get_organization_tree(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取组织架构树
        可选：指定学院ID获取特定学院的树形结构
        """
        if college_id:
            colleges = College.objects.filter(id=college_id, is_deleted=False)
        else:
            colleges = College.objects.filter(is_deleted=False)
        
        colleges = colleges.prefetch_related(
            'majors', 'majors__classes'
        ).order_by('code')
        
        tree_data = []
        for college in colleges:
            college_data = {
                'id': college.id,
                'code': college.code,
                'name': college.name,
                'type': 'college',
                'children': []
            }
            
            # 获取该学院下的专业
            majors = college.majors.filter(is_deleted=False).order_by('code')
            for major in majors:
                major_data = {
                    'id': major.id,
                    'code': major.code,
                    'name': major.name,
                    'type': 'major',
                    'duration_type': major.duration_type,
                    'duration_label': major.get_duration_label(),
                    'children': []
                }
                
                # 获取该专业下的班级
                classes = major.classes.filter(is_deleted=False).order_by('-enrollment_year', 'class_number')
                for school_class in classes:
                    class_data = {
                        'id': school_class.id,
                        'name': school_class.name,
                        'type': 'class',
                        'enrollment_year': school_class.enrollment_year,
                        'class_number': school_class.class_number,
                        'head_teacher': {
                            'employee_id': school_class.head_teacher.employee_id,
                            'name': school_class.head_teacher.name
                        } if school_class.head_teacher else None
                    }
                    major_data['children'].append(class_data)
                
                college_data['children'].append(major_data)
            
            tree_data.append(college_data)
        
        return tree_data
    
    def get_college_statistics(self, college: College) -> Dict[str, Any]:
        """
        获取学院统计信息
        """
        # 统计专业数量
        major_count = college.majors.filter(is_deleted=False).count()
        
        # 统计班级数量
        class_count = Class.objects.filter(major__college=college, is_deleted=False).count()
        
        # 统计教师数量
        teacher_count = college.teachers.filter(is_deleted=False).count()
        
        # 按学制类型统计专业数量
        duration_stats = college.majors.filter(is_deleted=False).values('duration_type').annotate(
            count=Count('id')
        )
        
        return {
            'college': {
                'id': college.id,
                'code': college.code,
                'name': college.name
            },
            'major_count': major_count,
            'class_count': class_count,
            'teacher_count': teacher_count,
            'duration_stats': list(duration_stats)
        }
    
    def get_major_statistics(self, major: Major) -> Dict[str, Any]:
        """
        获取专业统计信息
        """
        # 统计班级数量
        class_count = major.classes.filter(is_deleted=False).count()
        
        # 按入学年份统计班级数量
        enrollment_stats = major.classes.filter(is_deleted=False).values('enrollment_year').annotate(
            count=Count('id')
        ).order_by('-enrollment_year')
        
        return {
            'major': {
                'id': major.id,
                'code': major.code,
                'name': major.name
            },
            'class_count': class_count,
            'enrollment_stats': list(enrollment_stats)
        }
    
    def get_organization_statistics(self) -> Dict[str, Any]:
        """
        获取组织架构整体统计信息
        """
        # 统计学院数量
        college_count = College.objects.filter(is_deleted=False).count()
        
        # 统计专业数量
        major_count = Major.objects.filter(is_deleted=False).count()
        
        # 统计班级数量
        class_count = Class.objects.filter(is_deleted=False).count()
        
        # 按学院统计专业数量
        college_major_stats = College.objects.filter(is_deleted=False).annotate(
            major_count=Count('majors', filter=Q(majors__is_deleted=False))
        ).values('id', 'name', 'major_count').order_by('-major_count')
        
        # 按学制类型统计专业数量
        duration_stats = Major.objects.filter(is_deleted=False).values('duration_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 按入学年份统计班级数量
        enrollment_stats = Class.objects.filter(is_deleted=False).values('enrollment_year').annotate(
            count=Count('id')
        ).order_by('-enrollment_year')
        
        return {
            'total_colleges': college_count,
            'total_majors': major_count,
            'total_classes': class_count,
            'college_major_stats': list(college_major_stats),
            'duration_stats': list(duration_stats),
            'enrollment_stats': list(enrollment_stats)
        }
    
    def validate_class_naming(self, major: Major, enrollment_year: int, class_number: int) -> str:
        """
        验证并生成班级名称
        格式：{入学年份}年{专业名称}{学制标识}-{班级序号}班
        """
        # 获取学制标识
        duration_label = major.get_duration_label()
        
        # 生成班级名称
        name = f"{enrollment_year}年{major.name}{duration_label}-{class_number}班"
        
        # 检查班级名称是否已存在（同专业同年份）
        existing_class = Class.objects.filter(
            major=major,
            enrollment_year=enrollment_year,
            class_number=class_number,
            is_deleted=False
        ).first()
        
        if existing_class:
            raise ValidationError(f"班级名称已存在：{name}")
        
        return name
    
    def get_available_teachers_for_head_teacher(self, college: College, exclude_class_id: Optional[int] = None) -> list:
        """
        获取可担任班主任的教师列表
        排除已经是其他班级班主任的教师
        """
        from personnel.models import Teacher
        
        # 获取本学院的教师
        available_teachers = Teacher.objects.filter(
            college=college,
            is_deleted=False
        )
        
        # 排除已经是其他班级班主任的教师
        exclude_employee_ids = Class.objects.filter(
            is_deleted=False,
            head_teacher__isnull=False
        ).exclude(
            id=exclude_class_id
        ).values_list('head_teacher__employee_id', flat=True)
        
        available_teachers = available_teachers.exclude(
            employee_id__in=exclude_employee_ids
        )
        
        return list(available_teachers)
    
    def bulk_create_classes(self, classes_data: List[Dict[str, Any]], creator_id: int) -> List[Class]:
        """
        批量创建班级
        """
        created_classes = []
        
        with transaction.atomic():
            for class_data in classes_data:
                # 验证数据
                major_id = class_data.get('major_id')
                enrollment_year = class_data.get('enrollment_year')
                class_number = class_data.get('class_number')
                head_teacher_id = class_data.get('head_teacher_id')
                
                # 获取专业
                try:
                    major = Major.objects.get(id=major_id, is_deleted=False)
                except Major.DoesNotExist:
                    raise ValidationError(f"专业不存在：{major_id}")
                
                # 生成班级名称
                name = self.validate_class_naming(major, enrollment_year, class_number)
                
                # 创建班级
                school_class = Class.objects.create(
                    major=major,
                    name=name,
                    enrollment_year=enrollment_year,
                    class_number=class_number,
                    head_teacher_id=head_teacher_id if head_teacher_id else None,
                    student_count=class_data.get('student_count', 0),
                    description=class_data.get('description', '')
                )
                
                created_classes.append(school_class)
        
        return created_classes
    
    def validate_college_code(self, code: str) -> None:
        """
        验证学院代码格式
        应符合GB/T 13745标准（学科分类与代码）
        """
        import re
        
        # 基本格式验证：4位数字
        if not re.match(r'^\d{4}$', code):
            raise ValidationError("学院代码格式错误，应为4位数字")
        
        # 检查代码是否已存在
        if College.objects.filter(code=code, is_deleted=False).exists():
            raise ValidationError(f"学院代码已存在：{code}")
    
    def validate_major_code(self, code: str, college: College) -> None:
        """
        验证专业代码格式
        格式：2位专业序号
        """
        import re
        
        # 基本格式验证
        if not re.match(r'^\d{2}$', code):
            raise ValidationError("专业代码格式错误，应为2位数字")
        
        # 检查代码是否已存在
        if Major.objects.filter(code=code, is_deleted=False).exists():
            raise ValidationError(f"专业代码已存在：{code}")
    
    def validate_major_name_uniqueness(self, name: str, college: College, exclude_id: Optional[int] = None) -> None:
        """
        验证专业名称在同一学院下的唯一性
        """
        queryset = Major.objects.filter(
            name=name,
            college=college,
            is_deleted=False
        )
        
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if queryset.exists():
            raise ValidationError(f"专业名称在同一学院下已存在：{name}")
    
    def get_college_by_code(self, code: str) -> Optional[College]:
        """
        根据代码获取学院
        """
        try:
            return College.objects.get(code=code, is_deleted=False)
        except College.DoesNotExist:
            return None
    
    def get_major_by_code(self, code: str) -> Optional[Major]:
        """
        根据代码获取专业
        """
        try:
            return Major.objects.get(code=code, is_deleted=False)
        except Major.DoesNotExist:
            return None
