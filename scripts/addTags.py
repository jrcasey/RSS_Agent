import argparse
from pathlib import Path


def split_yaml_frontmatter(text: str) -> tuple[str, str | None, str]:
	bom = ""
	working = text
	if working.startswith("\ufeff"):
		bom = "\ufeff"
		working = working[1:]

	lines = working.splitlines(keepends=True)
	if not lines or lines[0].strip() != "---":
		return bom, None, working

	for idx, line in enumerate(lines[1:], start=1):
		if line.strip() == "---":
			frontmatter = "".join(lines[: idx + 1])
			body = "".join(lines[idx + 1 :])
			return bom, frontmatter, body

	return bom, None, working


def has_yaml_frontmatter(text: str) -> bool:
	_, frontmatter, _ = split_yaml_frontmatter(text)
	return frontmatter is not None


def build_frontmatter(tags: list[str]) -> str:
	lines = ["---", "tags:"]
	for tag in tags:
		lines.append(f"- {tag}")
	lines.append("---")
	return "\n".join(lines)


def normalize_tags(raw_tags: list[str]) -> list[str]:
	tags: list[str] = []
	seen = set()

	for raw in raw_tags:
		parts = [p.strip() for p in raw.split(",")]
		for part in parts:
			if not part:
				continue
			if part not in seen:
				seen.add(part)
				tags.append(part)

	return tags


def add_frontmatter_to_file(path: Path, tags: list[str]) -> bool:
	content = path.read_text(encoding="utf-8")
	if has_yaml_frontmatter(content):
		return False

	frontmatter = build_frontmatter(tags)
	new_content = f"{frontmatter}\n\n{content}" if content else f"{frontmatter}\n"
	path.write_text(new_content, encoding="utf-8")
	return True


def remove_frontmatter_from_file(path: Path) -> bool:
	content = path.read_text(encoding="utf-8")
	bom, frontmatter, body = split_yaml_frontmatter(content)
	if frontmatter is None:
		return False

	clean_body = body.lstrip("\r\n")
	path.write_text(f"{bom}{clean_body}", encoding="utf-8")
	return True


def remove_tag_from_frontmatter(frontmatter: str, tag_to_remove: str) -> tuple[str, bool]:
	lines = frontmatter.splitlines()
	if len(lines) < 2:
		return frontmatter, False

	content = lines[1:-1]
	tags_idx = None
	for i, line in enumerate(content):
		if line.strip().startswith("tags:"):
			tags_idx = i
			break

	if tags_idx is None:
		return frontmatter, False

	tags_line = content[tags_idx]
	base_indent = len(tags_line) - len(tags_line.lstrip(" "))
	after_colon = tags_line.split(":", 1)[1].strip()
	removed = False

	if after_colon.startswith("[") and after_colon.endswith("]"):
		raw_items = after_colon[1:-1]
		items = [item.strip() for item in raw_items.split(",") if item.strip()]
		new_items = [item for item in items if item != tag_to_remove]
		removed = len(new_items) != len(items)
		if removed:
			if new_items:
				content[tags_idx] = f"{' ' * base_indent}tags: [{', '.join(new_items)}]"
			else:
				del content[tags_idx]
	else:
		start = tags_idx + 1
		end = start
		list_items: list[tuple[int, str]] = []
		while end < len(content):
			line = content[end]
			stripped = line.strip()
			indent = len(line) - len(line.lstrip(" "))

			if stripped and indent <= base_indent and ":" in stripped:
				break

			if stripped.startswith("-"):
				value = stripped[1:].strip()
				list_items.append((end, value))

			end += 1

		if list_items:
			remaining_values = [value for _, value in list_items if value != tag_to_remove]
			removed = len(remaining_values) != len(list_items)
			if removed:
				if remaining_values:
					list_indent = " " * (base_indent + 2)
					new_list_lines = [f"{list_indent}- {value}" for value in remaining_values]
					content = content[:start] + new_list_lines + content[end:]
				else:
					content = content[:tags_idx] + content[end:]
		else:
			# Scalar form: tags: mytag
			value = after_colon
			if value == tag_to_remove:
				removed = True
				del content[tags_idx]

	if not removed:
		return frontmatter, False

	new_lines = ["---", *content, "---"]
	return "\n".join(new_lines), True


def remove_tag_from_file(path: Path, tag_to_remove: str) -> str:
	content = path.read_text(encoding="utf-8")
	bom, frontmatter, body = split_yaml_frontmatter(content)
	if frontmatter is None:
		return "no-frontmatter"

	updated_frontmatter, changed = remove_tag_from_frontmatter(frontmatter, tag_to_remove)
	if not changed:
		return "tag-not-found"

	frontmatter_lines = updated_frontmatter.splitlines()
	has_metadata = len(frontmatter_lines) > 2
	if has_metadata:
		new_content = f"{bom}{updated_frontmatter}\n\n{body.lstrip('\\r\\n')}"
	else:
		new_content = f"{bom}{body.lstrip('\\r\\n')}"

	path.write_text(new_content, encoding="utf-8")
	return "updated"


def main() -> None:
	parser = argparse.ArgumentParser(
		description=(
			"Add YAML frontmatter tags, remove a specific tag from frontmatter, "
			"or strip frontmatter from Markdown files in a directory."
		)
	)
	parser.add_argument("directory", help="Directory containing Markdown files")
	action_group = parser.add_mutually_exclusive_group(required=True)
	action_group.add_argument(
		"--tags",
		nargs="+",
		help="Tags to include (use space-separated values and/or comma-separated entries)",
	)
	action_group.add_argument(
		"--remove-tag",
		help="Tag to remove from existing frontmatter",
	)
	action_group.add_argument(
		"--remove-frontmatter",
		action="store_true",
		help="Remove YAML frontmatter block from Markdown files",
	)
	parser.add_argument(
		"--recursive",
		action="store_true",
		help="Include Markdown files in subdirectories",
	)

	args = parser.parse_args()

	target_dir = Path(args.directory)
	if not target_dir.exists() or not target_dir.is_dir():
		raise SystemExit(f"Directory not found: {target_dir}")

	pattern = "**/*.md" if args.recursive else "*.md"
	markdown_files = sorted(target_dir.glob(pattern))

	updated = 0
	skipped = 0

	mode = "add"
	tags: list[str] = []
	if args.tags is not None:
		tags = normalize_tags(args.tags)
		if not tags:
			raise SystemExit("No valid tags provided.")
		mode = "add"
	elif args.remove_tag is not None:
		mode = "remove-tag"
	else:
		mode = "remove-frontmatter"

	for md_file in markdown_files:
		if mode == "add":
			if add_frontmatter_to_file(md_file, tags):
				updated += 1
				print(f"Updated: {md_file}")
			else:
				skipped += 1
				print(f"Skipped (already has frontmatter): {md_file}")
		elif mode == "remove-tag":
			result = remove_tag_from_file(md_file, args.remove_tag)
			if result == "updated":
				updated += 1
				print(f"Updated: {md_file}")
			else:
				skipped += 1
				print(f"Skipped ({result}): {md_file}")
		else:
			if remove_frontmatter_from_file(md_file):
				updated += 1
				print(f"Updated: {md_file}")
			else:
				skipped += 1
				print(f"Skipped (no-frontmatter): {md_file}")

	print(f"Done. Updated {updated} file(s), skipped {skipped} file(s).")


if __name__ == "__main__":
	main()
