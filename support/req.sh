curl -i -F "license_plates=BB111" -F "longitude=12222" -F "latitude=33333" -F "city=Kiev" -F "address=Foo-baar 33/3" \
-F "images=@homer.png" -F "images=@duck.png" \
-F "types=Паркування на перехресті" -F "types=Тип порушення 2" -F "types=Тип порушення 3" \
http://127.0.0.1:8000/api/upload/
