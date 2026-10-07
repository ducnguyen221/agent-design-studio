import { Button } from './Button.js';
const button = Button('Show validation');
button.addEventListener('click', () => {
  document.querySelector('#feedback').textContent = 'Error: enter a value before continuing.';
});
document.querySelector('#actions').append(button);
