# Contributing to Content Moderation System

Thank you for your interest in contributing! This document provides guidelines for team collaboration.

## 🚀 Getting Started

1. **Fork the repository** (if external contributor)
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/content-moderation-system.git
   cd content-moderation-system
   ```
3. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8  # Dev dependencies
   ```

## 🌿 Branching Strategy

### Branch Naming Convention

- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes
- `docs/documentation-update` - Documentation changes
- `refactor/code-improvement` - Code refactoring

### Examples

```bash
git checkout -b feature/add-user-authentication
git checkout -b bugfix/fix-database-connection
git checkout -b docs/update-api-documentation
```

## 📝 Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
git commit -m "feat(api): add batch moderation endpoint"
git commit -m "fix(dashboard): resolve import error in analytics page"
git commit -m "docs(readme): update installation instructions"
git commit -m "test(inference): add unit tests for BERT predictor"
```

## 🔄 Pull Request Process

### Before Creating PR

1. **Update from main**:
   ```bash
   git checkout main
   git pull origin main
   git checkout your-branch
   git rebase main
   ```

2. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

3. **Format code**:
   ```bash
   black src/ api/ dashboard/
   flake8 src/ api/ dashboard/
   ```

4. **Update documentation** if needed

### Creating PR

1. **Push your branch**:
   ```bash
   git push origin your-branch
   ```

2. **Open Pull Request** on GitHub

3. **Fill out PR template**:
   - Description of changes
   - Related issue number (if applicable)
   - Testing performed
   - Screenshots (if UI changes)

4. **Request review** from team members

### PR Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages are clear
- [ ] Code is well-commented

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_inference.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_inference.py::test_predict_toxic -v
```

### Writing Tests

```python
# tests/test_example.py
import pytest
from src.module import function

def test_function_success():
    """Test successful case."""
    result = function("input")
    assert result == "expected"

def test_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        function("invalid")
```

### Test Coverage

- Aim for **80%+ coverage** for new code
- All new features must have tests
- Bug fixes should include regression tests

## 📋 Code Style Guidelines

### Python Style (PEP 8)

```python
# Good
def calculate_toxicity_score(text: str) -> float:
    """
    Calculate toxicity score for given text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Toxicity score between 0.0 and 1.0
    """
    # Implementation
    pass

# Bad
def calc(t):
    # No docstring, unclear names
    pass
```

### Formatting

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Imports**: Organized (stdlib, third-party, local)
- **Docstrings**: Google style

### Type Hints

```python
# Use type hints for function signatures
def moderate_text(
    text: str,
    threshold: float = 0.5
) -> Dict[str, Any]:
    pass
```

## 📁 Project Structure Guidelines

### Adding New Features

1. **Backend API**: Add to `api/`
   - Routes in `api/main.py`
   - Schemas in `api/schemas.py`
   - Business logic in `api/services.py`

2. **ML Models**: Add to `src/`
   - Training in `src/training/`
   - Inference in `src/inference/`

3. **Frontend**: Add to `dashboard/`
   - Keep `dashboard/app.py` organized
   - Use helper functions for components

4. **Tests**: Add to `tests/`
   - Mirror source structure
   - Name tests `test_*.py`

### File Naming

- Python files: `lowercase_with_underscores.py`
- Classes: `PascalCase`
- Functions: `lowercase_with_underscores`
- Constants: `UPPERCASE_WITH_UNDERSCORES`

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues
2. Verify it's reproducible
3. Test on latest version

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. Step three

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 10, macOS 12, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Browser (if applicable): [e.g., Chrome 95]

**Screenshots**
If applicable

**Additional Context**
Any other relevant information
```

## ✨ Feature Requests

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Any other relevant information
```

## 📚 Documentation Guidelines

### Code Documentation

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief one-line description.
    
    Longer description if needed. Explain what the function does,
    any important details, and edge cases.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
        
    Example:
        >>> result = complex_function("test", 5)
        >>> print(result)
        {'key': 'value'}
    """
    pass
```

### README Updates

- Keep README.md concise and high-level
- Add detailed docs to ARCHITECTURE.md
- Update QUICKSTART.md for setup changes

## 🔐 Security Guidelines

### Sensitive Data

- **Never commit** API keys, passwords, or secrets
- Use environment variables for configuration
- Add sensitive files to `.gitignore`

### Code Security

- Validate all user inputs
- Use parameterized queries for database
- Sanitize text before processing
- Follow OWASP guidelines

## 🎯 Areas for Contribution

### High Priority

- [ ] Add user authentication system
- [ ] Implement rate limiting
- [ ] Add Docker containerization
- [ ] Create CI/CD pipeline
- [ ] Improve test coverage

### Medium Priority

- [ ] Add multi-language support
- [ ] Implement custom moderation rules
- [ ] Add export functionality
- [ ] Create admin dashboard
- [ ] Add API documentation examples

### Low Priority

- [ ] UI/UX improvements
- [ ] Performance optimizations
- [ ] Additional chart types
- [ ] Mobile responsiveness
- [ ] Dark/light theme toggle

## 💬 Communication

### Channels

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code review and discussion
- **Discussions**: General questions and ideas

### Response Times

- **Critical bugs**: Within 24 hours
- **Pull requests**: Within 2-3 days
- **Feature requests**: Within 1 week

## 📖 Resources

### Documentation

- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Setup guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [Python PEP 8 Style Guide](https://pep8.org/)

## ❓ Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search closed issues
3. Open a new issue with the `question` label
4. Reach out to maintainers

## 🙏 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!

---

**Happy Contributing! 🚀**
