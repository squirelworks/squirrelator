"""Phase 4 intent grammar: parse English instructions into Intents."""

from squirrelator.intent import Intent, generate, parse_intent
from squirrelator.translator import _match_natural


def test_parse_output_print_and_bare_hello():
    assert parse_intent("print hello") == Intent("output", name="hello")
    assert parse_intent("show 'Good morning'") == Intent("output", name="good morning")
    assert parse_intent("say hello to everyone") == Intent("output", name="Hello")


def test_parse_loop_and_assignment():
    assert parse_intent("count from 1 to 5") == Intent("loop", start="1", end="5")
    assert parse_intent("loop 3 through 7") == Intent("loop", start="3", end="7")
    assert parse_intent("set total to 42") == Intent("assignment", name="total", start="42")
    assert parse_intent("make name = 'Ada'") == Intent(
        "assignment", name="name", start="'ada'"
    )
    assert parse_intent("set x to 3 plus 5") == Intent(
        "assignment", name="x", start="3 + 5"
    )
    assert parse_intent("set y to 10 minus 2") == Intent(
        "assignment", name="y", start="10 - 2"
    )
    assert parse_intent("let z = 4 times 3") == Intent(
        "assignment", name="z", start="4 * 3"
    )
    assert parse_intent("set q to 8 divided by 2") == Intent(
        "assignment", name="q", start="8 / 2"
    )


def test_parse_unknown_is_none():
    assert parse_intent("sort the list") is None
    assert parse_intent("") is None


def test_parse_input():
    assert parse_intent("ask for name") == Intent("input", name="name")
    assert parse_intent("ask the user for age") == Intent("input", name="age")
    assert parse_intent("input score") == Intent("input", name="score")
    assert parse_intent("read line from the user") == Intent("input", name="line")


def test_parse_function_that_prints():
    got = parse_intent("define a function greet that prints hello")
    assert got == Intent(
        "function", name="greet", body=Intent("output", name="hello")
    )
    got = parse_intent("create function sayhi that shows hi")
    assert got.kind == "function" and got.name == "sayhi" and got.body.name == "hi"


def test_parse_call():
    assert parse_intent("call greet") == Intent("call", name="greet")
    assert parse_intent("run the function sayhi") == Intent("call", name="sayhi")
    assert parse_intent("invoke total") == Intent("call", name="total")


def test_parse_list():
    got = parse_intent("make a list called items with a, b, c")
    assert got == Intent("list", name="items", start="a,b,c")
    got = parse_intent("create list nums of 1 2 3")
    assert got == Intent("list", name="nums", start="1,2,3")


def test_parse_map():
    got = parse_intent("make a map called ages with alice 30 bob 40")
    assert got == Intent("map", name="ages", start="alice=30;bob=40")
    got = parse_intent("create dictionary scores of math:90, english:85")
    assert got == Intent("map", name="scores", start="math=90;english=85")


def test_parse_file():
    assert parse_intent("read file data.txt") == Intent(
        "file", name="data.txt", start="read", end="text"
    )
    assert parse_intent("read file data.txt into body") == Intent(
        "file", name="data.txt", start="read", end="body"
    )
    assert parse_intent("write hello to file out.txt") == Intent(
        "file", name="out.txt", start="write", end="hello"
    )


def test_parse_if_then_print():
    got = parse_intent("if x > 5 print ready")
    assert got == Intent(
        "if", name="x", start=">", end="5", body=Intent("output", name="ready")
    )
    got = parse_intent("if count is greater than 10 then print full")
    assert got.kind == "if" and got.start == ">" and got.body.name == "full"


def test_parse_if_else_print():
    got = parse_intent("if x > 5 print ready else print wait")
    assert got == Intent(
        "if",
        name="x",
        start=">",
        end="5",
        body=Intent("output", name="ready"),
        alt=Intent("output", name="wait"),
    )
    got = parse_intent("if n is less than 3 then print small else print big")
    assert got.alt is not None and got.alt.name == "big" and got.start == "<"


def test_generate_python_matches_rules_shapes():
    assert generate(Intent("output", name="hello"), "python") == 'print("hello")'
    assert generate(Intent("loop", start="1", end="5"), "python") == (
        "for i in range(1, 6):\n    print(i)"
    )
    assert generate(Intent("assignment", name="total", start="42"), "python") == "total = 42"
    assert generate(Intent("input", name="name"), "python") == "name = input()"
    assert generate(Intent("input", name="name"), "javascript") == "let name = prompt();"
    assert generate(Intent("input", name="name"), "shell") == "read name"
    assert generate(Intent("input", name="name"), "cobol") == "ACCEPT name"
    assert generate(Intent("output", name="hi"), "cobol") == 'DISPLAY "hi"'
    assert generate(Intent("output", name="hi"), "c") == 'printf("hi\\n");'
    assert generate(Intent("output", name="hi"), "cpp") == (
        'std::cout << "hi" << std::endl;'
    )
    assert generate(Intent("output", name="hi"), "csharp") == 'Console.WriteLine("hi");'
    assert generate(Intent("output", name="hi"), "java") == 'System.out.println("hi");'
    assert generate(Intent("output", name="hi"), "rust") == 'println!("hi");'
    assert generate(Intent("output", name="hi"), "go") == 'fmt.Println("hi")'
    assert generate(Intent("output", name="hi"), "kotlin") == 'println("hi")'
    assert generate(Intent("output", name="hi"), "swift") == 'print("hi")'
    assert generate(Intent("loop", start="1", end="3"), "c") == (
        'for (int i = 1; i <= 3; i++) {\n  printf("%d\\n", i);\n}'
    )
    assert generate(Intent("loop", start="1", end="3"), "cpp") == (
        "for (int i = 1; i <= 3; i++) {\n  std::cout << i << std::endl;\n}"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "c") == "int x = 3 + 5;"
    assert generate(Intent("assignment", name="name", start='"ada"'), "c") == (
        'char *name = "ada";'
    )
    assert generate(Intent("assignment", name="name", start='"ada"'), "cpp") == (
        'std::string name = "ada";'
    )
    assert generate(Intent("input", name="n"), "c") == 'int n;\nscanf("%d", &n);'
    assert generate(Intent("input", name="n"), "cpp") == "int n;\nstd::cin >> n;"
    fn = Intent("function", name="greet", body=Intent("output", name="hello"))
    assert generate(fn, "python") == 'def greet():\n    print("hello")'
    assert generate(fn, "javascript") == 'function greet() {\n  console.log("hello");\n}'
    assert generate(fn, "shell") == 'greet() {\n  echo "hello"\n}'
    assert generate(fn, "c") == 'void greet(void) {\n  printf("hello\\n");\n}'
    assert generate(fn, "cpp") == (
        'void greet() {\n  std::cout << "hello" << std::endl;\n}'
    )
    assert generate(fn, "csharp") == (
        'void greet() {\n  Console.WriteLine("hello");\n}'
    )
    assert generate(fn, "java") == (
        'void greet() {\n  System.out.println("hello");\n}'
    )
    assert generate(fn, "cobol") == 'GREET.\n  DISPLAY "hello"'
    assert generate(Intent("call", name="greet"), "python") == "greet()"
    assert generate(Intent("call", name="greet"), "javascript") == "greet();"
    assert generate(Intent("call", name="greet"), "c") == "greet();"
    assert generate(Intent("call", name="greet"), "cpp") == "greet();"
    assert generate(Intent("call", name="greet"), "cobol") == "PERFORM greet"
    lst = Intent("list", name="items", start="a,b,c")
    assert generate(lst, "python") == 'items = ["a", "b", "c"]'
    assert generate(lst, "javascript") == 'let items = ["a", "b", "c"];'
    assert generate(Intent("list", name="nums", start="1,2,3"), "python") == "nums = [1, 2, 3]"
    assert generate(Intent("list", name="nums", start="1,2,3"), "c") == "int nums[] = {1, 2, 3};"
    assert generate(lst, "c") == 'const char *items[] = {"a", "b", "c"};'
    assert generate(Intent("list", name="nums", start="1,2,3"), "cpp") == (
        "std::vector<int> nums = {1, 2, 3};"
    )
    assert generate(lst, "cpp") == 'std::vector<std::string> items = {"a", "b", "c"};'
    assert generate(lst, "csharp") == (
        'var items = new List<string> { "a", "b", "c" };'
    )
    assert generate(lst, "java") == (
        'java.util.List<String> items = java.util.List.of("a", "b", "c");'
    )
    assert generate(lst, "cobol") == '* list items: "a", "b", "c"'
    mp = Intent("map", name="ages", start="alice=30;bob=40")
    assert generate(mp, "python") == 'ages = {"alice": 30, "bob": 40}'
    assert generate(mp, "javascript") == 'let ages = {"alice": 30, "bob": 40};'
    assert generate(mp, "c") == (
        'const char *ages_keys[] = {"alice", "bob"};\n'
        "int ages_vals[] = {30, 40};"
    )
    assert generate(mp, "cpp") == (
        'std::map<std::string, int> ages = {{"alice", 30}, {"bob", 40}};'
    )
    assert generate(mp, "csharp") == (
        'var ages = new Dictionary<string, int> { { "alice", 30 }, { "bob", 40 } };'
    )
    assert generate(mp, "cobol") == '* map ages: "alice" => 30, "bob" => 40'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "python") == (
        'text = open("data.txt").read()'
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hello"), "python") == (
        'open("out.txt", "w").write("hello")'
    )
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "c") == (
        'char text[1024];\n'
        'FILE *f = fopen("data.txt", "r");\n'
        "if (f) { fgets(text, sizeof text, f); fclose(f); }"
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "cpp") == (
        'std::ofstream out("out.txt");\nout << "hi";'
    )
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "cobol") == "* read data.txt into text"
    iff = Intent("if", name="x", start=">", end="5", body=Intent("output", name="ready"))
    assert generate(iff, "python") == 'if x > 5:\n    print("ready")'
    assert generate(iff, "javascript") == 'if (x > 5) {\n  console.log("ready");\n}'
    assert generate(iff, "c") == 'if (x > 5) {\n  printf("ready\\n");\n}'
    assert generate(iff, "cpp") == (
        'if (x > 5) {\n  std::cout << "ready" << std::endl;\n}'
    )
    ifelse = Intent(
        "if",
        name="x",
        start=">",
        end="5",
        body=Intent("output", name="ready"),
        alt=Intent("output", name="wait"),
    )
    assert generate(ifelse, "python") == (
        'if x > 5:\n    print("ready")\nelse:\n    print("wait")'
    )
    assert generate(ifelse, "javascript") == (
        'if (x > 5) {\n  console.log("ready");\n}'
        ' else {\n  console.log("wait");\n}'
    )
    assert generate(ifelse, "shell") == (
        'if [ "$x" -gt 5 ]; then\n  echo "ready"\nelse\n  echo "wait"\nfi'
    )
    assert generate(ifelse, "c") == (
        'if (x > 5) {\n  printf("ready\\n");\n}'
        ' else {\n  printf("wait\\n");\n}'
    )


    assert generate(Intent("loop", start="1", end="3"), "swift") == (
        "for i in 1...3 {\n  print(i)\n}"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "swift") == "var x = 3 + 5"
    assert generate(Intent("input", name="n"), "swift") == 'let n = readLine() ?? ""'
    assert generate(fn, "swift") == 'func greet() {\n  print("hello")\n}'
    assert generate(Intent("call", name="greet"), "swift") == "greet()"
    assert generate(lst, "swift") == 'let items = ["a", "b", "c"]'
    assert generate(mp, "swift") == 'let ages = ["alice": 30, "bob": 40]'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "swift") == (
        'let text = try! String(contentsOfFile: "data.txt")'
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "swift") == (
        'try! "hi".write(toFile: "out.txt", atomically: true, encoding: .utf8)'
    )
    assert generate(iff, "swift") == 'if (x > 5) {\n  print("ready")\n}'
    assert generate(ifelse, "swift") == (
        'if (x > 5) {\n  print("ready")\n}'
        ' else {\n  print("wait")\n}'
    )

    assert generate(Intent("output", name="hi"), "typescript") == 'console.log("hi");'
    assert generate(Intent("loop", start="1", end="3"), "typescript") == (
        "for (let i = 1; i <= 3; i++) {\n  console.log(i);\n}"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "typescript") == "let x = 3 + 5;"
    assert generate(Intent("input", name="n"), "typescript") == "let n = prompt();"
    assert generate(fn, "typescript") == (
        'function greet() {\n  console.log("hello");\n}'
    )
    assert generate(Intent("call", name="greet"), "typescript") == "greet();"
    assert generate(lst, "typescript") == 'let items = ["a", "b", "c"];'
    assert generate(mp, "typescript") == 'let ages = {"alice": 30, "bob": 40};'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "typescript") == (
        'const fs = require("fs");\n'
        'let text = fs.readFileSync("data.txt", "utf8");'
    )
    assert generate(iff, "typescript") == (
        'if (x > 5) {\n  console.log("ready");\n}'
    )
    assert generate(ifelse, "typescript") == (
        'if (x > 5) {\n  console.log("ready");\n}'
        ' else {\n  console.log("wait");\n}'
    )

    assert generate(Intent("output", name="hi"), "php") == 'echo "hi\\n";'
    assert generate(Intent("loop", start="1", end="3"), "php") == (
        'for ($i = 1; $i <= 3; $i++) {\n  echo "$i\\n";\n}'
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "php") == "$x = 3 + 5;"
    assert generate(Intent("input", name="n"), "php") == "$n = trim(fgets(STDIN));"
    assert generate(fn, "php") == 'function greet() {\n  echo "hello\\n";\n}'
    assert generate(Intent("call", name="greet"), "php") == "greet();"
    assert generate(lst, "php") == '$items = ["a", "b", "c"];'
    assert generate(mp, "php") == '$ages = ["alice" => 30, "bob" => 40];'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "php") == (
        '$text = file_get_contents("data.txt");'
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "php") == (
        'file_put_contents("out.txt", "hi");'
    )
    assert generate(iff, "php") == 'if ($x > 5) {\n  echo "ready\\n";\n}'
    assert generate(ifelse, "php") == (
        'if ($x > 5) {\n  echo "ready\\n";\n}'
        ' else {\n  echo "wait\\n";\n}'
    )


    assert generate(Intent("output", name="hi"), "perl") == 'print "hi\\n";'
    assert generate(Intent("loop", start="1", end="3"), "perl") == (
        'for (my $i = 1; $i <= 3; $i++) {\n  print "$i\\n";\n}'
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "perl") == "my $x = 3 + 5;"
    assert generate(Intent("input", name="n"), "perl") == "chomp(my $n = <>);"
    assert generate(fn, "perl") == 'sub greet {\n  print "hello\\n";\n}'
    assert generate(Intent("call", name="greet"), "perl") == "greet();"
    assert generate(lst, "perl") == 'my @items = ("a", "b", "c");'
    assert generate(mp, "perl") == 'my %ages = ("alice" => 30, "bob" => 40);'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "perl") == (
        'open my $fh, "<", "data.txt" or die $!;\n'
        'local $/; my $text = <$fh>;\n'
        "close $fh;"
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "perl") == (
        'open my $fh, ">", "out.txt" or die $!;\n'
        'print $fh "hi";\n'
        "close $fh;"
    )
    assert generate(iff, "perl") == 'if ($x > 5) {\n  print "ready\\n";\n}'
    assert generate(ifelse, "perl") == (
        'if ($x > 5) {\n  print "ready\\n";\n}'
        ' else {\n  print "wait\\n";\n}'
    )


    assert generate(Intent("output", name="hi"), "sql") == "SELECT 'hi' AS message;"
    assert generate(Intent("loop", start="1", end="3"), "sql") == (
        "-- count from 1 to 3\n"
        "WITH RECURSIVE seq(i) AS (\n"
        "  SELECT 1\n"
        "  UNION ALL\n"
        "  SELECT i + 1 FROM seq WHERE i < 3\n"
        ")\n"
        "SELECT i FROM seq;"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "sql") == (
        "-- set x\nSELECT 3 + 5 AS x;"
    )
    assert generate(Intent("input", name="n"), "sql") is None
    assert generate(fn, "sql") == "-- function greet\n-- SELECT 'hello' AS message;"
    assert generate(Intent("call", name="greet"), "sql") == "SELECT greet();"
    assert generate(lst, "sql") == (
        "-- list items\nSELECT * FROM (VALUES ('a', 'b', 'c')) AS items;"
    )
    assert generate(mp, "sql") == (
        "-- map ages\nSELECT * FROM (VALUES ('alice', 30), ('bob', 40)) AS ages(k, v);"
    )
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "sql") == (
        "-- read data.txt into text\n-- \\copy text FROM 'data.txt';"
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "sql") == (
        "-- write out.txt\n-- \\copy (SELECT 'hi') TO 'out.txt';"
    )
    assert generate(iff, "sql") == "SELECT CASE WHEN x > 5 THEN 'ready' END AS result;"
    assert generate(ifelse, "sql") == (
        "SELECT CASE WHEN x > 5 THEN 'ready' ELSE 'wait' END AS result;"
    )


    assert generate(Intent("output", name="hi"), "html") == 'document.write("hi");'
    assert generate(Intent("loop", start="1", end="3"), "html") == (
        "for (let i = 1; i <= 3; i++) {\n"
        "  document.write(i + '<br>');\n"
        "}"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "html") == "let x = 3 + 5;"
    assert generate(Intent("input", name="n"), "html") == "let n = prompt();"
    assert generate(fn, "html") == (
        "function greet() {\n  document.write(\"hello\");\n}"
    )
    assert generate(Intent("call", name="greet"), "html") == "greet();"
    assert generate(lst, "html") == 'let items = ["a", "b", "c"];'
    assert generate(mp, "html") == 'let ages = {"alice": 30, "bob": 40};'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "html") == (
        '// read data.txt\n'
        'fetch("data.txt").then(r => r.text()).then(t => { text = t; });'
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "html") == (
        "// write out.txt: hi"
    )
    assert generate(iff, "html") == (
        "if (x > 5) {\n  document.write(\"ready\");\n}"
    )
    assert generate(ifelse, "html") == (
        "if (x > 5) {\n"
        "  document.write(\"ready\");\n"
        "} else {\n"
        "  document.write(\"wait\");\n"
        "}"
    )


    assert generate(Intent("output", name="hi"), "vbnet") == 'Console.WriteLine("hi")'
    assert generate(Intent("loop", start="1", end="3"), "vbnet") == (
        "For i As Integer = 1 To 3\n"
        "  Console.WriteLine(i)\n"
        "Next"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "vbnet") == "Dim x = 3 + 5"
    assert generate(Intent("input", name="n"), "vbnet") == "Dim n = Console.ReadLine()"
    assert generate(fn, "vbnet") == (
        "Sub greet()\n  Console.WriteLine(\"hello\")\nEnd Sub"
    )
    assert generate(Intent("call", name="greet"), "vbnet") == "greet()"
    assert generate(lst, "vbnet") == 'Dim items = {"a", "b", "c"}'
    assert generate(mp, "vbnet") == (
        'Dim ages As New Dictionary(Of Object, Object) From '
        '{{"alice", 30}, {"bob", 40}}'
    )
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "vbnet") == (
        'Dim text = System.IO.File.ReadAllText("data.txt")'
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "vbnet") == (
        'System.IO.File.WriteAllText("out.txt", "hi")'
    )
    assert generate(iff, "vbnet") == (
        "If x > 5 Then\n  Console.WriteLine(\"ready\")\nEnd If"
    )
    assert generate(ifelse, "vbnet") == (
        "If x > 5 Then\n"
        "  Console.WriteLine(\"ready\")\n"
        "Else\n"
        "  Console.WriteLine(\"wait\")\n"
        "End If"
    )


    assert generate(Intent("output", name="hi"), "fortran") == 'print *, "hi"'
    assert generate(Intent("loop", start="1", end="3"), "fortran") == (
        "do i = 1, 3\n  print *, i\nend do"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "fortran") == "x = 3 + 5"
    assert generate(Intent("input", name="n"), "fortran") == "read *, n"
    assert generate(fn, "fortran") == (
        'subroutine greet()\n  print *, "hello"\nend subroutine greet'
    )
    assert generate(Intent("call", name="greet"), "fortran") == "call greet()"
    assert generate(Intent("list", name="items", start="1,2,3"), "fortran") == "items = [1, 2, 3]"
    assert generate(mp, "fortran") == '! map ages: "alice" => 30, "bob" => 40'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "fortran") == (
        'open(10, file="data.txt", status="old")\n'
        "read(10, *) text\n"
        "close(10)"
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "fortran") == (
        'open(10, file="out.txt", status="replace")\n'
        'write(10, *) "hi"\n'
        "close(10)"
    )
    assert generate(iff, "fortran") == (
        'if (x > 5) then\n  print *, "ready"\nend if'
    )
    assert generate(ifelse, "fortran") == (
        'if (x > 5) then\n'
        '  print *, "ready"\n'
        "else\n"
        '  print *, "wait"\n'
        "end if"
    )


    assert generate(Intent("loop", start="1", end="3"), "cobol") == (
        "PERFORM VARYING I FROM 1 BY 1 UNTIL I > 3\n"
        "  DISPLAY I\n"
        "END-PERFORM"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "cobol") == "MOVE 3 + 5 TO x"
    assert generate(iff, "cobol") == (
        'IF x > 5\n  DISPLAY "ready"\nEND-IF'
    )
    assert generate(ifelse, "cobol") == (
        "IF x > 5\n"
        '  DISPLAY "ready"\n'
        "ELSE\n"
        '  DISPLAY "wait"\n'
        "END-IF"
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "cobol") == (
        "* write out.txt: hi"
    )


    assert generate(Intent("output", name="hi"), "basic") == 'PRINT "hi"'
    assert generate(Intent("loop", start="1", end="3"), "basic") == (
        "FOR I = 1 TO 3\n  PRINT I\nNEXT I"
    )
    assert generate(Intent("assignment", name="x", start="3 + 5"), "basic") == "LET x = 3 + 5"
    assert generate(Intent("input", name="n"), "basic") == "INPUT n"
    assert generate(fn, "basic") == (
        'SUB greet\n  PRINT "hello"\nEND SUB'
    )
    assert generate(Intent("call", name="greet"), "basic") == "CALL greet"
    assert generate(lst, "basic") == 'DIM items(2)\n* "a", "b", "c"'
    assert generate(mp, "basic") == '\' map ages: "alice" => 30, "bob" => 40'
    assert generate(Intent("file", name="data.txt", start="read", end="text"), "basic") == (
        'OPEN "data.txt" FOR INPUT AS #1\nINPUT #1, text\nCLOSE #1'
    )
    assert generate(Intent("file", name="out.txt", start="write", end="hi"), "basic") == (
        'OPEN "out.txt" FOR OUTPUT AS #1\nPRINT #1, "hi"\nCLOSE #1'
    )
    assert generate(iff, "basic") == (
        'IF x > 5 THEN\n  PRINT "ready"\nEND IF'
    )
    assert generate(ifelse, "basic") == (
        "IF x > 5 THEN\n"
        '  PRINT "ready"\n'
        "ELSE\n"
        '  PRINT "wait"\n'
        "END IF"
    )


def test_match_natural_uses_intent_without_changing_outputs():
    assert _match_natural("print hello", "python") == ("output", 'print("hello")')
    assert _match_natural("count from 1 to 5", "python")[0] == "loop"
    assert _match_natural("set x to 1", "python") == ("assignment", "x = 1")
    assert _match_natural("set x to 3 plus 5", "python") == ("assignment", "x = 3 + 5")
    assert _match_natural("ask for name", "python") == ("input", "name = input()")
    assert _match_natural(
        "define a function greet that prints hello", "python"
    ) == ("function", 'def greet():\n    print("hello")')
    assert _match_natural("call greet", "python") == ("call", "greet()")
    assert _match_natural("make a list called items with a b c", "python") == (
        "list",
        'items = ["a", "b", "c"]',
    )
    assert _match_natural("make a map called ages with alice 30 bob 40", "python") == (
        "map",
        'ages = {"alice": 30, "bob": 40}',
    )
    assert _match_natural("read file data.txt", "python") == (
        "file",
        'text = open("data.txt").read()',
    )
    assert _match_natural("sort the list", "python")[0] is None
    assert _match_natural("if x > 5 print ready", "python") == (
        "if",
        'if x > 5:\n    print("ready")',
    )
    assert _match_natural("if x > 5 print ready else print wait", "python") == (
        "if",
        'if x > 5:\n    print("ready")\nelse:\n    print("wait")',
    )
