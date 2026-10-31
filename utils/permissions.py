from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    自定义权限：只允许对象的创建者或相关用户访问。
    """

    def has_object_permission(self, request, view, obj):
        # 对于安全方法（如 GET、HEAD 或 OPTIONS），允许所有用户访问
        if request.method in permissions.SAFE_METHODS:
            return True

        # 针对 Issue & Video 模型的权限控制
        if hasattr(obj, 'author'):
            return obj.author == request.user

        # 针对 Picture 模型的权限控制
        if hasattr(obj, 'issue') and hasattr(obj.issue, 'author'):
            return obj.issue.author == request.user

        # 针对 Character 模型的权限控制
        if hasattr(obj, 'belongs_to'):
            return obj.belongs_to == request.user

        # 默认拒绝访问
        return False