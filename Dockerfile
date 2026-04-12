# Dockerfile for building the interpreter, tester, and check tools
# Author: Marek Gašpierik (xgaspim00)

#####################################################
# Stage 1: Quality check tools (ruff, mypy, eslint) #
#####################################################
# Use python:3.14-rc-slim as the base image for the check stage
FROM python:3.14-rc-slim AS check

# Install Node.js 24.12 for running ESLint and Prettier
COPY --from=node:24.12-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:24.12-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

# Copy dependency definitions for the interpreter
COPY python/int/requirements.txt /tmp/int-requirements.txt
COPY python/int/requirements-dev.txt /tmp/int-requirements-dev.txt
# Install project requirements and development dependencies
RUN pip install --no-cache-dir \
    -r /tmp/int-requirements.txt \
    -r /tmp/int-requirements-dev.txt

# Copy dependency definitions for the TypeScript tester
COPY typescript/tester/package.json typescript/tester/package-lock.json /tmp/tester/
# Install dependencies for the linter (ESLint) and formatter (Prettier)
RUN cd /tmp/tester && npm ci

# Add node_modules binaries to PATH so tools can be executed directly
ENV PATH="/tmp/tester/node_modules/.bin:$PATH"

# Set the working directory to /src for running checks
WORKDIR /

# Entry point for this image is shell
ENTRYPOINT ["/bin/bash"]

####################################
# Stage 2: Build TypeScript tester #
####################################

FROM node:24.12-slim AS build-test


WORKDIR /app
# Copy config files for clean installation of dependencies
COPY typescript/tester/package.json typescript/tester/package-lock.json ./
RUN npm ci

# Copy tester source codes and tsconfig for compilation
COPY typescript/tester/src/ src/
COPY typescript/tester/tsconfig.json .
# Compile the tester
RUN npx tsc

################################
# Stage 3: Runtime interpreter #
################################

FROM python:3.14-rc-slim AS runtime

WORKDIR /app
# Copy requirements for the interpreter
COPY python/int/requirements.txt .
# Install system dependencies required to compile lxml (gcc, XML/XSLT and zlib headers)
# and git for cloning sol2xml from the templates repository
RUN apt-get update && apt-get install -y gcc libxml2-dev libxslt1-dev zlib1g-dev git && \
    rm -rf /var/lib/apt/lists/*
# Clone sol2xml from the templates repository at a pinned commit for reproducibility
RUN git clone https://github.com/iondryas/ipp26-project-templates.git /tmp/templates && \
    git -C /tmp/templates checkout 1d9245f82a7504e64999c04003f6edf1c5556681 && \
    cp -r /tmp/templates/sol2xml /sol2xml && \
    rm -rf /tmp/templates
# Install requirements for the interpreter and sol2xml
RUN pip install --no-cache-dir -r requirements.txt -r /sol2xml/requirements.txt

# Copy the interpreter source codes into the image
COPY python/int/src/ src/

# The image directly runs the interpreter
ENTRYPOINT ["python", "src/solint.py"]

####################################
# Stage 4: Test (runtime + tester) #
####################################
FROM runtime AS test

# Install Node.js 24.12
COPY --from=node:24.12-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:24.12-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

# Copy the compiled tester and its dependencies from the build-test stage
COPY --from=build-test /app/dist/ /tester/dist/
COPY --from=build-test /app/node_modules/ /tester/node_modules/

# Define paths to necessary components
ENV SOL2XML="python /sol2xml/sol_to_xml.py"
ENV INTERPRETER="python /app/src/solint.py"

# Runs testing tool
ENTRYPOINT ["node", "/tester/dist/tester.js"]
