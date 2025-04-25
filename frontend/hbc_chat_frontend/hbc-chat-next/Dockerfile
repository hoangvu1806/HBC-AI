FROM node:22-alpine

EXPOSE 3030

# RUN apk update && apk add --no-cache bash coreutils && apk add --no-cache npm

WORKDIR /app
COPY ./ ./

RUN npm install
RUN npm run build

CMD ["npm", "start"]