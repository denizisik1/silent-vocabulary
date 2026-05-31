### Const

- Clear leftover packages, requirements and code.
- Sanitize for certain words.
- Add universal/shortcuts.py file if it is not going to make the code too convoluted.

### UI

- Make it more suitable to multiple language support.
- Add color theme.
- Add fonts.
- Write better and more comprehensive tests, especially for "retrieve" logic, remove leftovers from older states of the projects that do not make sense to have now.

### Possible Changes

- IPA (only the relevant letters) in the toast notification too?
- Debug console.

### Decide

- Pulling IPA from wiki pages?

### Later

- Consider adding pyinstaller.
- Support for Windows.

### Next
- Resultbox should have a seperator for seperating results.
- Resultbox should have a clear button for clearing results, although cleared results should not be truly removed but rather hidden and could be seen when clicked on a conveniently placed button.
- When "fetch ipa" button is clicked resultsbox automatically scrolls to the top, it should stick to the bottom like a regular bash terminal would since newer results pile at the bottom.
- The "pip install -r requirements" alone won't install all the needed components like zendriver, when zendriver is called if it is not installed a GUI popup should appear and ask user approval and if given install it.
