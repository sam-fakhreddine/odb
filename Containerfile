FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal
ARG EMULATOR_PACKAGE=aws-emulator-aarch64.rpm
COPY ${EMULATOR_PACKAGE} /tmp/aws-emulator.rpm
RUN rpm -i /tmp/aws-emulator.rpm && rm /tmp/aws-emulator.rpm \
    && mkdir -p /home/emulator/.aws/emulator && chown -R 1000:1000 /home/emulator
USER 1000
ENV HOME=/home/emulator
ENTRYPOINT ["aws-emulator", "--bind", "0.0.0.0"]
