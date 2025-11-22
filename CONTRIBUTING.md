# Contributing to AI Agent Tool-Calling Guide

First off, thank you for considering contributing to this project! 🎉

This repository aims to be the go-to educational resource for AI agent tool-calling, and contributions from the community are what make it great.

## 🌟 How Can You Contribute?

### 1. Documentation Improvements
- Fix typos, grammar, or unclear explanations
- Add more detailed explanations to existing topics
- Create new documentation for uncovered areas
- Improve code comments and examples

### 2. Code Examples
- Add examples in new programming languages
- Improve existing examples with better practices
- Create minimal reproducible examples for concepts
- Add error handling and edge cases

### 3. Projects and Tutorials
- Build new end-to-end project tutorials
- Improve existing project documentation
- Add setup instructions for different environments
- Create video walkthroughs

### 4. Bug Fixes
- Fix broken code examples
- Update outdated dependencies
- Correct technical inaccuracies
- Fix broken links

### 5. Design Assets
- Create or improve diagrams
- Design architecture visualizations
- Add flowcharts and illustrations

## 📋 Contribution Process

### Step 1: Find or Create an Issue
- Browse [existing issues](https://github.com/yourusername/ai-agent-tool-calling/issues)
- Comment on issues you'd like to work on
- Create a new issue for major changes before starting work

### Step 2: Fork and Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/ai-agent-tool-calling.git
cd ai-agent-tool-calling
git remote add upstream https://github.com/ORIGINAL_OWNER/ai-agent-tool-calling.git
```

### Step 3: Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Step 4: Make Your Changes
- Follow the style guide (see below)
- Test your code examples
- Update documentation as needed
- Add yourself to contributors if this is your first contribution

### Step 5: Commit Your Changes
```bash
git add .
git commit -m "feat: add description of your changes"

# Use conventional commits:
# feat: new feature
# fix: bug fix
# docs: documentation changes
# style: formatting changes
# refactor: code refactoring
# test: adding tests
# chore: maintenance tasks
```

### Step 6: Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Detailed description of what and why
- Reference to related issues
- Screenshots/GIFs if applicable

## 📝 Style Guide

### Documentation Style
- **Use clear, concise language**: Avoid jargon unless necessary
- **Include examples**: Every concept should have a code example
- **Add diagrams**: Visual aids improve understanding
- **Break up text**: Use headings, bullet points, and short paragraphs (3-5 sentences max)
- **Use second person**: Write "you" instead of "we" or "one"
- **Provide context**: Explain why, not just how

### Code Style

#### Python
```python
# Follow PEP 8
# Use type hints
# Add docstrings

def calculator_tool(expression: str) -> str:
    """
    Evaluates a mathematical expression safely.
    
    Args:
        expression: A valid Python mathematical expression
        
    Returns:
        The result of the calculation as a string
        
    Raises:
        ValueError: If the expression is invalid
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")
```

#### Markdown
- Use headings hierarchically (# for title, ## for sections, etc.)
- Add line breaks between sections
- Use code fences with language specification
- Include alt text for images
- Keep lines under 120 characters where possible

#### File Organization
```
docs/
  ├── 01-introduction.md      # Use numbered prefixes for order
  ├── 02-fundamentals.md
  └── images/                 # Keep images organized
      └── architecture.png

examples/
  ├── python-basic/
  │   ├── README.md          # Each example needs a README
  │   ├── requirements.txt   # Pin dependencies
  │   └── example.py
```

### Example Requirements
Every code example should:
- ✅ Run without errors
- ✅ Include a README with setup instructions
- ✅ List all dependencies with versions
- ✅ Include comments explaining key concepts
- ✅ Handle errors gracefully
- ✅ Be as simple as possible while demonstrating the concept

## 🧪 Testing Your Changes

### Documentation
- Read through your changes for clarity
- Check all links work
- Verify code examples run correctly
- Preview Markdown rendering

### Code Examples
```bash
# Install dependencies
pip install -r requirements.txt

# Run the example
python examples/your-example/main.py

# Run tests if applicable
pytest tests/
```

## 🎯 Good First Issues

Look for issues labeled `good first issue` or `help wanted`. These are great entry points for new contributors.

## 💡 Contribution Ideas

### High-Impact Contributions
- Adding examples in new languages (TypeScript, Rust, Go)
- Creating video tutorials
- Writing case studies of real-world implementations
- Building interactive demos
- Adding performance benchmarks

### Quick Wins
- Fixing typos
- Improving code comments
- Adding error handling to examples
- Creating diagrams for existing concepts
- Writing tests for examples

## ❓ Questions?

- **Before starting major work**: Open an issue to discuss your idea
- **Need help?**: Comment on an issue or start a discussion
- **Found a security issue?**: Email directly (don't open a public issue)

## 📜 Code of Conduct

This project adheres to a code of conduct. By participating, you agree to:
- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

## 🏆 Recognition

Contributors will be:
- Added to the contributors list
- Credited in release notes for significant contributions
- Mentioned in documentation they helped create

## 📚 Resources for Contributors

### Learning Resources
- [Markdown Guide](https://www.markdownguide.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Write Good Documentation](https://www.writethedocs.org/guide/)

### Project-Specific Resources
- [UTCP Specification](https://www.utcp.io/)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [LangChain Documentation](https://docs.langchain.com/)

## 🔄 Keeping Your Fork Updated

```bash
# Fetch latest changes
git fetch upstream

# Merge into your local main
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

## ✅ Pull Request Checklist

Before submitting your PR, ensure:
- [ ] Code examples run without errors
- [ ] Documentation is clear and well-formatted
- [ ] All links are working
- [ ] Commit messages follow conventional commits
- [ ] Branch is up-to-date with main
- [ ] You've tested your changes
- [ ] README updated if adding new examples/projects

## 🎉 Thank You!

Every contribution, no matter how small, makes a difference. Thank you for helping make this the best resource for learning about AI agent tool-calling!

---

**Questions or suggestions about this contributing guide?** Open an issue or discussion!


