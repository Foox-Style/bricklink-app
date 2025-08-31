# Claude Code Notes for BrickLink App

## Important Reminders

### Unicode Encoding Issues
**CRITICAL**: This Windows environment has encoding issues with Unicode characters in console output.

**Problem**: Using Unicode characters like arrows (→, ←, ↑, ↓) or other special symbols in print statements causes:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position X: character maps to <undefined>
```

**Solution**: Always use ASCII alternatives:
- Use `->` instead of `→`
- Use `<-` instead of `←`
- Use `^` instead of `↑`
- Use `v` instead of `↓`
- Use `*` instead of `•`
- Use regular quotes `'` instead of smart quotes `'` or `"`

**Files affected**: Any file with console output, especially test files and debug output.

## Development Commands

### Testing
- `python location_matcher.py` - Test location matching logic
- `python bsx_handler.py` - Test BSX file handling
- `python main_app.py` - Run the GUI application

### Linting/Type Checking
(Add commands here if they exist in the project)

## Project Structure Notes
- `location_matcher.py` - Core location assignment logic (color-based)
- `bsx_handler.py` - BSX file parsing and manipulation
- `main_app.py` - GUI application
- `bricklink_api.py` - BrickLink API integration
- `config.json` - API credentials storage