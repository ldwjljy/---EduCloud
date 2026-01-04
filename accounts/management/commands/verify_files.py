from django.core.management.base import BaseCommand, CommandError
import os
import hashlib
import json
from datetime import datetime


def file_hash(path, algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stat_info(path):
    st = os.stat(path)
    return {
        'size': st.st_size,
        'mtime': int(st.st_mtime),
        'readonly': bool(st.st_file_attributes & 0x1) if hasattr(st, 'st_file_attributes') else False,
    }


class Command(BaseCommand):
    help = '文件迁移完整性校验：生成校验表并比对源/目标目录，校验大小、MD5、SHA256、修改时间、权限属性'

    def add_arguments(self, parser):
        parser.add_argument('--src', required=True, help='源目录绝对路径')
        parser.add_argument('--dst', required=True, help='目标目录绝对路径')
        parser.add_argument('--output', default='migration_file_report.json', help='输出报告路径')

    def handle(self, *args, **options):
        src = options['src']
        dst = options['dst']
        out = options['output']
        if not os.path.isabs(src) or not os.path.isdir(src):
            raise CommandError('源目录路径无效')
        if not os.path.isabs(dst) or not os.path.isdir(dst):
            raise CommandError('目标目录路径无效')

        def walk_dir(root):
            table = {}
            for base, _, files in os.walk(root):
                for name in files:
                    p = os.path.join(base, name)
                    rel = os.path.relpath(p, root)
                    info = stat_info(p)
                    entry = {
                        'source_path': os.path.abspath(p),
                        'size': info['size'],
                        'mtime': info['mtime'],
                        'md5': file_hash(p, 'md5'),
                        'sha256': file_hash(p, 'sha256'),
                        'readonly': info['readonly'],
                    }
                    table[rel.replace('\\', '/')] = entry
            return table

        src_table = walk_dir(src)
        dst_table = walk_dir(dst)

        mismatches = []
        missing_dst = []
        extra_dst = []

        for rel, s in src_table.items():
            d = dst_table.get(rel)
            if not d:
                missing_dst.append({'relative': rel, 'source': s['source_path']})
                continue
            issues = {}
            if s['size'] != d['size']:
                issues['size'] = {'src': s['size'], 'dst': d['size']}
            if s['md5'] != d['md5']:
                issues['md5'] = {'src': s['md5'], 'dst': d['md5']}
            if s['sha256'] != d['sha256']:
                issues['sha256'] = {'src': s['sha256'], 'dst': d['sha256']}
            if s['readonly'] != d['readonly']:
                issues['readonly'] = {'src': s['readonly'], 'dst': d['readonly']}
            # 允许轻微时间戳差异（复制时可能发生），仅记录但不判定失败
            if s['mtime'] != d['mtime']:
                issues['mtime'] = {'src': s['mtime'], 'dst': d['mtime']}
            if issues:
                mismatches.append({'relative': rel, 'issues': issues})

        for rel in dst_table.keys():
            if rel not in src_table:
                extra_dst.append({'relative': rel, 'target': dst_table[rel]['source_path']})

        passed = (len(src_table) == len(dst_table)) and not mismatches and not missing_dst and not extra_dst
        report = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'source_root': os.path.abspath(src),
            'target_root': os.path.abspath(dst),
            'source_count': len(src_table),
            'target_count': len(dst_table),
            'requirements': {
                'count_match': True,
                'content_identical': True,
                'permissions_preserved': True,
            },
            'results': {
                'count_match': len(src_table) == len(dst_table),
                'content_identical': not mismatches and not missing_dst,
                'permissions_preserved': all(not m['issues'].get('readonly') for m in mismatches),
            },
            'missing_in_target': missing_dst,
            'extra_in_target': extra_dst,
            'mismatches': mismatches,
        }

        # 简单数字签名（SHA256）
        body = json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8')
        signature = hashlib.sha256(body).hexdigest()
        report['signature_sha256'] = signature

        with open(out, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        if not passed:
            raise CommandError('文件迁移校验未通过，详见报告：%s' % out)

        self.stdout.write(self.style.SUCCESS('文件迁移校验通过，报告已生成：%s' % out))

