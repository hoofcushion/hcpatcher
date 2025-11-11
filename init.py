import json
import shutil
from pathlib import Path
from typing import Any, Optional, Union, List, Tuple, Dict

TRANSLATION_CACHE_FILE = Path("dict_cache.json")

def parse_path(path: str) -> List[Union[str, int]]:
    return [int(k) if k.isdigit() else k for k in path.split(".")] if path else []

def index(container: Any, key: Union[str, int]) -> Optional[Any]:
    if isinstance(key, int) and isinstance(container, list) and 0 <= key < len(container):
        return container[key]
    elif isinstance(container, dict) and key in container:
        return container[key]
    return None

def newindex(container: Any, key: Union[str, int], value: Any) -> bool:
    if isinstance(key, int) and isinstance(container, list) and 0 <= key < len(container):
        container[key] = value
        return True
    elif isinstance(container, dict) and key in container:
        container[key] = value
        return True
    return False

def get_nested_value(data: Any, keys: List[Union[str, int]]) -> Optional[Any]:
    current = data
    for key in keys:
        current = index(current, key)
        if current is None:
            return None
    return current

def apply_patch(data: Any, path: str, operation: str, value: Any) -> Tuple[Any, bool, Optional[str]]:
    keys = parse_path(path)
    if not keys:
        if operation == "/=":
            return value, True, None
        return data, False, f"Invalid operation '{operation}' for root"
    parent_keys = keys[:-1] if keys else []
    last_key = keys[-1] if keys else None
    parent_data = get_nested_value(data, parent_keys)
    if parent_data is None:
        return data, False, f"Path not found: {'.'.join(str(k) for k in parent_keys)}"
    if last_key is None:
        return data, False, f"Invalid path: {path}"
    old_val = index(parent_data, last_key)
    if old_val is None:
        return data, False, f"Key not found or index out of range: {path}"
    if operation == "/=":
        if newindex(parent_data, last_key, value):
            return data, True, None
        return data, False, f"Assignment failed: {path}"
    elif operation == "/-":
        if isinstance(last_key, int) and isinstance(parent_data, list):
            parent_data.pop(last_key)
        elif isinstance(parent_data, dict):
            parent_data.pop(last_key)
        else:
            return data, False, f"Cannot delete from non-container: {path}"
        return data, True, None
    elif operation.startswith("/+"):
        if not isinstance(old_val, list):
            return data, False, f"Target is not a list: {path}"
        if operation == "/+$":
            old_val.append(value)
        elif operation == "/+^":
            old_val.insert(0, value)
        elif operation.startswith("/+"):
            try:
                index_val = int(operation[2:])
                if index_val < -1 or index_val >= len(old_val):
                    return data, False, f"Index out of range: {index_val}"
                old_val.insert(index_val + 1, value)
            except ValueError:
                return data, False, f"Invalid index: {operation[2:]}"
        else:
            return data, False, f"Unknown operation: {operation}"
        return data, True, None
    return data, False, f"Unknown operation: {operation}"

def apply_patch_with_translation(
    data: Any,
    path: str,
    operation: str,
    value: Any,
    filename: str = "",
    translation_cache: Optional[Dict[str, str]] = None,
) -> Tuple[Any, bool, Optional[str]]:
    actual = value
    if value == "<translate>" and translation_cache is not None and filename and path:
        old_val = get_nested_value(data, parse_path(path))
        if old_val and isinstance(old_val, str):
            field_path = path if path else "root"
            actual = get_cached_translation(translation_cache, filename, field_path, old_val)
    return apply_patch(data, path, operation, actual)

def apply_patch_with_log(
    data: Any,
    path: str,
    operation: str,
    value: Any,
    filename: str = "",
    translation_cache: Optional[Dict[str, str]] = None,
) -> Tuple[Any, bool, Optional[str], Optional[Any], Optional[Any]]:
    old_val = get_nested_value(data, parse_path(path))
    result, ok, err = apply_patch_with_translation(data, path, operation, value, filename, translation_cache)
    new_val = get_nested_value(result, parse_path(path))
    return (result, ok, err, old_val, new_val)

def load_translation_cache() -> Dict[str, str]:
    if TRANSLATION_CACHE_FILE.exists():
        with open(TRANSLATION_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_translation_cache(cache: Dict[str, str]) -> None:
    with open(TRANSLATION_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def translate_text(text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
    try:
        from translate import Translator
        translator = Translator(from_lang=source_lang, to_lang=target_lang)
        return translator.translate(text)
    except Exception as e:
        print(f"翻译失败: {e}, 返回原文: {text}")
        return text

def get_cached_translation(
    cache: Dict[str, str], filename: str, field_path: str, original_text: str
) -> str:
    cache_key = f"{filename}:{field_path}"
    if cache_key in cache:
        return cache[cache_key]
    translated = translate_text(original_text)
    cache[cache_key] = translated
    save_translation_cache(cache)
    print(f"翻译缓存: {original_text} -> {translated}")
    return translated

def deep_merge_patches(base: Dict[str, Dict[str, Any]], new: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """深度合并补丁，相同文件的补丁操作会合并而不是覆盖"""
    result = base.copy()
    for filename, file_patches in new.items():
        if filename in result:
            # 合并相同文件的补丁操作
            result[filename].update(file_patches)
        else:
            result[filename] = file_patches
    return result

def load_patches_from_directory(patches_dir: Path) -> Dict[str, Dict[str, Any]]:
    """从 patches 文件夹加载所有 JSON 补丁文件，深度合并"""
    patches = {}
    if not patches_dir.exists():
        print(f"错误: patches 文件夹不存在: {patches_dir}")
        return patches
    
    patch_files = sorted(patches_dir.glob("*.json"))
    if not patch_files:
        print(f"错误: patches 文件夹中没有找到 JSON 文件: {patches_dir}")
        return patches
    
    for patch_file in patch_files:
        try:
            with open(patch_file, "r", encoding="utf-8") as f:
                file_patches = json.load(f)
                patches = deep_merge_patches(patches, file_patches)
            print(f"加载补丁文件: {patch_file.name}")
        except Exception as e:
            print(f"错误: 无法加载补丁文件 {patch_file}: {e}")
    
    return patches

def test_functions():
    print("===测试核心函数===")
    assert parse_path("a.b.0") == ["a", "b", 0]
    assert parse_path("") == []
    print("✓ parse_path 测试通过")
    data = {"a": [1, 2, {"b": "value"}]}
    val = index(data, "a")
    assert val == [1, 2, {"b": "value"}]
    val = index(val, 2)
    assert val == {"b": "value"}
    val = index(val, "b")
    assert val == "value"
    print("✓ index 测试通过")
    test_dict = {"x": 1}
    assert newindex(test_dict, "x", 2)
    assert test_dict["x"] == 2
    test_list = [1, 2, 3]
    assert newindex(test_list, 1, 99)
    assert test_list[1] == 99
    print("✓ newindex 测试通过")
    val = get_nested_value(data, ["a", 2, "b"])
    assert val == "value"
    print("✓ get_nested_value 测试通过")
    test_data = {"name": "Knight's Sword", "damage": 10}
    result, ok, err = apply_patch(test_data, "name", "/=", "骑士之剑")
    assert ok and result["name"] == "骑士之剑"
    result, ok, err = apply_patch(test_data, "damage", "/-", None)
    assert ok and "damage" not in result
    test_list_data = {"items": ["a", "b"]}
    result, ok, err = apply_patch(test_list_data, "items", "/+$", "c")
    assert ok and result["items"] == ["a", "b", "c"]
    print("✓ apply_patch 测试通过")

def process_patches() -> None:
    source_dir, output_dir, patches_dir, diff_log_file = (
        Path("source"),
        Path("output"),
        Path("patches"),
        Path("diff.log"),
    )
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 只从 patches 文件夹加载补丁
    patches = load_patches_from_directory(patches_dir)
    
    if not patches:
        print("错误: 未找到任何补丁文件")
        return
    
    translation_cache = load_translation_cache()
    print(f"加载翻译缓存: {len(translation_cache)} 条记录")
    print(f"加载补丁总数: {sum(len(file_patches) for file_patches in patches.values())} 个操作")
    
    total, success, diff_log, failed = 0, 0, [], []
    for filename, file_patches in patches.items():
        source_path = source_dir / filename
        if not source_path.exists():
            print(f"Warning: {source_path} not found")
            continue
        with open(source_path, "r", encoding="utf-8") as f:
            data: Any = json.load(f)
        for path_op, val in file_patches.items():
            total += 1
            path, op = path_op.rsplit("/", 1) if "/" in path_op else ("", "/=")
            op = "/" + op if "/" in path_op else op
            data, ok, err, old, new = apply_patch_with_log(data, path, op, val, filename, translation_cache)
            if ok:
                success += 1
                diff_log.append(f"{filename}: {path_op} | {repr(old)} -> {repr(new)}")
            else:
                failed.append({"file": filename, "op": path_op, "val": val, "err": err})
                print(f"Warning: {filename} - {path_op}: {err}")
        with open(output_dir / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    with open(diff_log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(diff_log))
    print(f"Summary: {total} total, {success} successful, {len(failed)} failed")
    if diff_log:
        print("\nChanges:\n" + "\n".join(f"  {e}" for e in diff_log))
    if failed:
        print("\nFailed:\n" + "\n".join(f"  {f['file']}: {f['op']} - {f['err']}" for f in failed))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_functions()
        print("\n🎉 所有测试通过！")
    else:
        process_patches()
