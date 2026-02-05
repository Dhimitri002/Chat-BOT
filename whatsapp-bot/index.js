const wppconnect = require('@wppconnect-team/wppconnect');
const axios = require('axios');

wppconnect.create({
  session: 'bot1'
}).then(client => {
  client.onMessage(async message => {
    if (message.isGroupMsg) return;

    const res = await axios.post('http://localhost:8000/chat', {
      text: message.body
    });

    await client.sendText(message.from, res.data.reply);
  });
});
