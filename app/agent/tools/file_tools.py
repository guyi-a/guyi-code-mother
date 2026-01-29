"""
文件操作工具 - 供Agent调用
"""
import os
import re
import glob
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果数据类"""
    file_path: str
    line_number: int
    line_content: str
    match_groups: Optional[List[str]] = None
    matched_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content.strip(),
            "matched_text": self.matched_text,
            "match_groups": self.match_groups
        }


def _validate_path(workspace_path: str, file_path: str) -> Path:
    """
    验证并规范化文件路径，确保在workspace_path目录下
    
    Args:
        workspace_path: 工作区根路径
        file_path: 相对路径或文件名
        
    Returns:
        规范化后的完整路径
        
    Raises:
        ValueError: 如果路径超出工作区范围
    """
    # 规范化工作区路径
    workspace = Path(workspace_path).resolve()
    
    # 处理相对路径
    if os.path.isabs(file_path):
        # 如果是绝对路径，检查是否在工作区内
        target = Path(file_path).resolve()
        try:
            target.relative_to(workspace)
        except ValueError:
            raise ValueError(f"路径 {file_path} 超出工作区范围")
        return target
    else:
        # 相对路径，拼接工作区路径
        target = (workspace / file_path).resolve()
        # 再次验证是否在工作区内（防止路径遍历攻击）
        try:
            target.relative_to(workspace)
        except ValueError:
            raise ValueError(f"路径 {file_path} 超出工作区范围")
        return target


def mkdir(workspace_path: str, dir_path: str) -> str:
    """
    创建文件夹（如果不存在）
    
    Args:
        workspace_path: 工作区根路径
        dir_path: 要创建的文件夹路径（相对于workspace_path）
        
    Returns:
        成功消息
    """
    try:
        full_path = _validate_path(workspace_path, dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建文件夹: {full_path}")
        return f"成功创建文件夹: {dir_path}"
    except Exception as e:
        error_msg = f"创建文件夹失败: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def write_file(workspace_path: str, file_path: str, content: str) -> str:
    """
    写入文件（如果文件不存在则创建，存在则覆盖）
    
    Args:
        workspace_path: 工作区根路径
        file_path: 文件路径（相对于workspace_path）
        content: 文件内容
        
    Returns:
        成功消息
    """
    try:
        full_path = _validate_path(workspace_path, file_path)
        # 确保父目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        # 写入文件
        full_path.write_text(content, encoding='utf-8')
        logger.info(f"写入文件: {full_path}")
        return f"成功写入文件: {file_path}"
    except Exception as e:
        error_msg = f"写入文件失败: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def read_file(workspace_path: str, file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        workspace_path: 工作区根路径
        file_path: 文件路径（相对于workspace_path）
        
    Returns:
        文件内容
    """
    try:
        full_path = _validate_path(workspace_path, file_path)
        if not full_path.exists():
            raise ValueError(f"文件不存在: {file_path}")
        if not full_path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")
        content = full_path.read_text(encoding='utf-8')
        logger.info(f"读取文件: {full_path}")
        return content
    except Exception as e:
        error_msg = f"读取文件失败: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def list_dir(workspace_path: str, dir_path: str = ".") -> List[str]:
    """
    列出目录内容
    
    Args:
        workspace_path: 工作区根路径
        dir_path: 目录路径（相对于workspace_path，默认为当前目录）
        
    Returns:
        目录下的文件和文件夹列表
    """
    try:
        full_path = _validate_path(workspace_path, dir_path)
        if not full_path.exists():
            raise ValueError(f"目录不存在: {dir_path}")
        if not full_path.is_dir():
            raise ValueError(f"路径不是目录: {dir_path}")
        items = [item.name for item in full_path.iterdir()]
        logger.info(f"列出目录: {full_path}, 共 {len(items)} 项")
        return sorted(items)
    except Exception as e:
        error_msg = f"列出目录失败: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def grep_search(
    workspace_path: str,
    search_path: str,
    pattern: str,
    file_pattern: Optional[str] = "**/*",
    case_sensitive: bool = False,
    recursive: bool = True,
    include_line_numbers: bool = True,
    max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    在指定路径中搜索匹配正则表达式的内容。
    
    Args:
        workspace_path: 工作区根路径
        search_path: 搜索的根目录路径（相对于workspace_path）
        pattern: 要搜索的正则表达式模式
        file_pattern: 要搜索的文件模式（如 "*.py", "**/*.txt"），默认搜索所有文件
        case_sensitive: 是否区分大小写，默认为 False
        recursive: 是否递归搜索子目录，默认为 True
        include_line_numbers: 是否包含行号，默认为 True
        max_results: 最大返回结果数，默认为 100
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    try:
        results = []
        # 验证并规范化搜索路径，确保在workspace_path内
        search_root = _validate_path(workspace_path, search_path)
        
        if not search_root.exists():
            logger.warning(f"Search path not found: {search_path}")
            return [{"error": f"Search path not found: {search_path}"}]
        
        if not search_root.is_dir():
            logger.warning(f"Search path is not a directory: {search_path}")
            return [{"error": f"Search path is not a directory: {search_path}"}]
            
        # 编译正则表达式
        regex_flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled_pattern = re.compile(pattern, regex_flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return [{"error": f"Invalid regex pattern: {e}"}]
        
        # 构建搜索路径
        if recursive:
            search_glob = str(search_root / "**" / file_pattern.lstrip("./"))
        else:
            search_glob = str(search_root / file_pattern.lstrip("./"))
        
        # 查找匹配的文件
        try:
            matched_files = []
            for file_path_str in glob.glob(search_glob, recursive=recursive):
                file_path = Path(file_path_str)
                if file_path.is_file():
                    # 确保文件在workspace_path内
                    try:
                        file_path.resolve().relative_to(Path(workspace_path).resolve())
                        matched_files.append(file_path)
                    except ValueError:
                        # 文件不在工作区内，跳过
                        continue
                    
            logger.info(f"Found {len(matched_files)} files to search in {search_path}")
            
        except Exception as e:
            logger.error(f"Error finding files: {e}")
            return [{"error": f"Error finding files: {e}"}]
        
        # 搜索文件内容
        for file_path in matched_files[:100]:  # 限制搜索的文件数量
            if len(results) >= max_results:
                break
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if len(results) >= max_results:
                            break
                            
                        match = compiled_pattern.search(line)
                        if match:
                            # 获取相对于workspace_path的相对路径
                            try:
                                rel_path = str(file_path.relative_to(Path(workspace_path).resolve()))
                            except ValueError:
                                # 如果无法计算相对路径，使用相对于搜索根目录的路径
                                try:
                                    rel_path = str(file_path.relative_to(search_root))
                                except ValueError:
                                    rel_path = str(file_path)
                                
                            result = SearchResult(
                                file_path=rel_path,
                                line_number=line_num if include_line_numbers else None,
                                line_content=line,
                                matched_text=match.group(),
                                match_groups=list(match.groups()) if match.groups() else []
                            )
                            results.append(result.to_dict())
                            
            except (UnicodeDecodeError, PermissionError, OSError) as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        # 返回结果信息
        if not results and matched_files:
            return [{
                "info": f"No matches found for pattern '{pattern}' in {len(matched_files)} files",
                "pattern": pattern,
                "files_searched": len(matched_files),
                "search_path": str(search_root)
            }]
        elif not matched_files:
            return [{
                "info": f"No files found matching pattern '{file_pattern}' in {search_path}",
                "file_pattern": file_pattern,
                "search_path": str(search_root)
            }]
        
        return results
        
    except Exception as e:
        logger.exception(f"Unexpected error in grep_search: {e}")
        return [{"error": str(e)}]


def glob_files(
    workspace_path: str,
    search_path: str,
    pattern: str,
    recursive: bool = True,
    include_dirs: bool = False,
    include_files: bool = True,
    sort_results: bool = True
) -> List[str]:
    """
    使用 glob 模式匹配文件和目录。
    
    Args:
        workspace_path: 工作区根路径
        search_path: 搜索的根目录路径（相对于workspace_path）
        pattern: glob 模式（如 "*.py", "**/*.txt", "*.md"）
        recursive: 是否递归匹配，默认为 True
        include_dirs: 是否包含目录，默认为 False
        include_files: 是否包含文件，默认为 True
        sort_results: 是否对结果进行排序，默认为 True
        
    Returns:
        List[str]: 匹配的路径列表（相对于workspace_path）
    """
    try:
        # 验证并规范化搜索路径，确保在workspace_path内
        root_path = _validate_path(workspace_path, search_path)
        
        if not root_path.exists():
            logger.warning(f"Search path not found: {search_path}")
            return []
        
        if not root_path.is_dir():
            logger.warning(f"Search path is not a directory: {search_path}")
            return []
        
        # 构建完整的 glob 模式
        full_pattern = str(root_path / pattern.lstrip("./"))
        
        try:
            # 使用 glob 查找匹配项
            matched_paths = []
            workspace_root = Path(workspace_path).resolve()
            
            for path_str in glob.glob(full_pattern, recursive=recursive):
                path_obj = Path(path_str)
                
                # 确保路径在workspace_path内
                try:
                    path_obj.resolve().relative_to(workspace_root)
                except ValueError:
                    # 路径不在工作区内，跳过
                    continue
                
                # 根据参数过滤
                if (include_dirs and path_obj.is_dir()) or (include_files and path_obj.is_file()):
                    # 获取相对于workspace_path的路径
                    try:
                        rel_path = str(path_obj.relative_to(workspace_root))
                    except ValueError:
                        # 如果无法计算相对路径，使用相对于搜索根目录的路径
                        try:
                            rel_path = str(path_obj.relative_to(root_path))
                        except ValueError:
                            rel_path = str(path_obj)
                    matched_paths.append(rel_path)
            
            # 可选排序
            if sort_results:
                matched_paths.sort()
            
            logger.info(f"Found {len(matched_paths)} matches for pattern '{pattern}' in {search_path}")
            return matched_paths
            
        except Exception as e:
            logger.error(f"Error in glob pattern matching: {e}")
            return []
            
    except Exception as e:
        logger.exception(f"Unexpected error in glob_files: {e}")
        return []


def get_file_tools(workspace_path: str) -> List[StructuredTool]:
    """
    获取文件操作工具列表
    
    Args:
        workspace_path: 工作区根路径
        
    Returns:
        工具列表
    """
    # 使用 functools.partial 绑定 workspace_path
    from functools import partial
    
    return [
        StructuredTool.from_function(
            func=partial(mkdir, workspace_path),
            name="mkdir",
            description="创建文件夹（如果不存在）。参数：dir_path - 要创建的文件夹路径（相对于工作区根路径）"
        ),
        StructuredTool.from_function(
            func=partial(write_file, workspace_path),
            name="write_file",
            description="写入文件（如果文件不存在则创建，存在则覆盖）。参数：file_path - 文件路径（相对于工作区根路径），content - 文件内容"
        ),
        StructuredTool.from_function(
            func=partial(read_file, workspace_path),
            name="read_file",
            description="读取文件内容。参数：file_path - 文件路径（相对于工作区根路径）"
        ),
        StructuredTool.from_function(
            func=partial(list_dir, workspace_path),
            name="list_dir",
            description="列出目录内容。参数：dir_path - 目录路径（相对于工作区根路径，默认为当前目录）"
        ),
        StructuredTool.from_function(
            func=partial(grep_search, workspace_path),
            name="grep_search",
            description="在指定路径中搜索匹配正则表达式的内容。参数：search_path - 搜索的根目录路径（相对于工作区根路径），pattern - 要搜索的正则表达式模式，file_pattern - 要搜索的文件模式（如 '*.py'，默认 '**/*'），case_sensitive - 是否区分大小写（默认False），recursive - 是否递归搜索（默认True），include_line_numbers - 是否包含行号（默认True），max_results - 最大返回结果数（默认100）"
        ),
        StructuredTool.from_function(
            func=partial(glob_files, workspace_path),
            name="glob_files",
            description="使用 glob 模式匹配文件和目录。参数：search_path - 搜索的根目录路径（相对于工作区根路径），pattern - glob 模式（如 '*.py'，'**/*.txt'），recursive - 是否递归匹配（默认True），include_dirs - 是否包含目录（默认False），include_files - 是否包含文件（默认True），sort_results - 是否对结果排序（默认True）"
        ),
    ]

