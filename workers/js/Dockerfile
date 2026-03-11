FROM node:24-alpine

RUN npm install -g nodemon

WORKDIR /app

COPY package.json ./

RUN npm install

COPY index.js ./

USER node

CMD ["nodemon", "--legacy-watch","--exec", "node","index.js"]