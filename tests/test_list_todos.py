import list_todos as m


def test_finds_shortcode_and_plain_todos(tmp_path):
    md = tmp_path / "about.md"
    md.write_text("---\ntitle: About\n---\n\n## Clusters\n\nFour clusters. {{< todo >}}(Matt) confirm cluster names{{< /todo >}}\n")
    toml = tmp_path / "hugo.toml"
    toml.write_text('title = "x"\n# TODO (Matt): set the form URL\n')
    found = m.find_todos([md, toml])
    assert [(p.name, line) for p, line, _ in found] == [("about.md", 7), ("hugo.toml", 2)]
    assert "confirm cluster names" in found[0][2]
    assert "set the form URL" in found[1][2]


def test_main_reports_and_exits_zero(tmp_path, capsys):
    (tmp_path / "a.md").write_text("{{< todo >}}(Matt) x{{< /todo >}}\n")
    assert m.main([str(tmp_path)]) == 0
    assert "a.md:1:" in capsys.readouterr().out


def test_ignores_examples_in_code_blocks(tmp_path):
    md = tmp_path / "README.md"
    md.write_text("Intro\n\n```\nExample {{< todo >}}(Matt) x{{< /todo >}}\n```\n\nReal {{< todo >}}(Matt) y{{< /todo >}}\n")
    assert [text for _, _, text in m.find_todos([md])] == ["(Matt) y"]


def test_ignores_inline_code(tmp_path):
    md = tmp_path / "README.md"
    md.write_text("Delete the whole `{{< todo >}}…{{< /todo >}}` when done.\n")
    assert m.find_todos([md]) == []
